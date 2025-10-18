# =========================
# File: tests/conftest.py
# =========================
import os
import importlib.util
from pathlib import Path
import pytest

def _locate_app_py(project_root: Path) -> Path:
    # Prefer /app/app.py; fallback to /app.py; else search.
    candidates = [
        project_root / "app" / "app.py",
        project_root / "app.py",
    ]
    for c in candidates:
        if c.exists():
            return c
    for p in project_root.rglob("app.py"):
        return p
    raise FileNotFoundError(f"Could not find app.py under {project_root}")

@pytest.fixture(scope="session")
def app_module(tmp_path_factory):
    project_root = Path(__file__).resolve().parents[1]
    app_file = _locate_app_py(project_root)

    # Import module from file path as "hoppi_app"
    spec = importlib.util.spec_from_file_location("hoppi_app", str(app_file))
    hoppi_app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hoppi_app)

    return hoppi_app

@pytest.fixture
def client(app_module, tmp_path, monkeypatch):
    # Redirect writable dirs
    uploads = tmp_path / "uploads"
    results = tmp_path / "results"
    os.environ["UPLOAD_FOLDER"] = str(uploads)
    os.environ["RESULTS_DIR"] = str(results)

    uploads.mkdir(parents=True, exist_ok=True)
    results.mkdir(parents=True, exist_ok=True)

    # Update Flask config + module-level constant
    app_module.app.config["UPLOAD_FOLDER"] = str(uploads)
    if hasattr(app_module, "RESULTS_DIR"):
        app_module.RESULTS_DIR = str(results)

    # ---- Stub outbound HTTP calls ----
    class _FakeResp:
        def __init__(self, data=None, status=200):
            self._data = data or {}
            self.status_code = status
        def json(self):
            return self._data
        def raise_for_status(self):
            if not (200 <= self.status_code < 300):
                raise RuntimeError(f"HTTP {self.status_code}")

    def _fake_http(url, **kw):
        if "sunrise-sunset.org" in url:
            # Fixed sunrise/sunset → ensures deterministic day period mapping
            return _FakeResp({"results": {
                "sunrise": "2025-06-01T07:00:00+00:00",
                "sunset":  "2025-06-01T20:00:00+00:00",
            }})
        if "open-meteo.com" in url:
            return _FakeResp({"current_weather": {"weathercode": 2}})  # cloudy
        if "nominatim.openstreetmap.org" in url:
            # Make location_type resolve to park
            return _FakeResp({"address": {"leisure": "park", "name": "Central Park"}})
        if "overpass-api.de" in url:
            # One nearby place, deterministic
            return _FakeResp({"elements": [{
                "lat": 49.2801, "lon": -123.1207,
                "tags": {"name": "Riverside Park", "leisure": "park"}
            }]})
        return _FakeResp({}, 404)

    monkeypatch.setattr(app_module, "http_get", _fake_http, raising=True)

    # ---- Stub LLM to deterministic string ----
    def _fake_llm(prompt: str) -> str:
        # short, <=35 words, ends with a nudge (per your rules)
        return "Touch something green nearby, snap a quick photo, and jot one sentence about how it made you feel. Try a new task after!"
    monkeypatch.setattr(app_module, "prompt_llm", _fake_llm, raising=True)

    # Flask testing client
    app = app_module.app
    app.testing = True
    return app.test_client()

# Handy coordinates used across tests
@pytest.fixture
def coords():
    return {"latitude": 49.2827, "longitude": -123.1207}  # Vancouver-ish
