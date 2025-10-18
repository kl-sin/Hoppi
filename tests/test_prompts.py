
import io
import json
from pathlib import Path
from typing import Optional

def test_generate_task_builds_rich_prompt(monkeypatch, client, coords, app_module):
    captured = {"prompt": None}

    def _capture_llm(prompt: str) -> str:
        captured["prompt"] = prompt
        return "Do a small creative act nearby and try another task!"
    monkeypatch.setattr(app_module, "prompt_llm", _capture_llm, raising=True)

    r = client.post("/generate-task", json=coords)
    assert r.status_code == 200
    # Assert prompt had the expected context
    p = captured["prompt"]
    assert isinstance(p, str) and len(p) > 0
    assert "You are a warm, witty real-world assistant named Hoppi." in p
    assert "Coordinates:" in p and f"{coords['latitude']:.4f}" in p
    assert "Nearby info:" in p                        # includes our stubbed Riverside Park line
    assert "Variation:" in p and "Freshness:" in p    # ensures those sections are present
    # sanity: response used our stubbed answer
    assert r.get_json()["task"].startswith("Do a small creative act")

def test_submit_uses_llm_verdict(monkeypatch, client, coords, app_module, tmp_path):
    verdict = "Nice shot! Keep the momentum and try one more challenge."
    monkeypatch.setattr(app_module, "prompt_llm", lambda _: verdict, raising=True)

    data = {
        "session_id": "llm1",
        "task": "Take a photo of something green",
        "media_type": "photo",
        "lat": str(coords["latitude"]),
        "lon": str(coords["longitude"]),
    }
    # small fake file
    r = client.post("/submit",
                    data={**data, "file": (io.BytesIO(b"img"), "pic.jpg")},
                    content_type="multipart/form-data")
    assert r.status_code == 200
    j = r.get_json()
    assert j["ok"] is True
    assert j["judge_text"] == verdict  # exact LLM output propagated

def judge_submission(
        task: str,
        media_type: str,
        text: Optional[str],
        file_path: Optional[str],
        lat: Optional[float],
        lon: Optional[float]
    ) -> str:
    def _boom(prompt: str):
        raise RuntimeError("LLM unavailable")
    monkeypatch.setattr(app_module, "prompt_llm", _boom, raising=True)

    r = client.post("/submit",
                    data={"session_id": "llm2", "task": "Any", "media_type": "text", "text": "hello"},
                    content_type="multipart/form-data")
    assert r.status_code == 200
    assert "Nice! That totally counts" in r.get_json()["judge_text"]

def test_generate_task_fallback_on_llm_error(monkeypatch, client, coords, app_module):
    def _boom(prompt: str):
        raise RuntimeError("LLM is down")
    
    monkeypatch.setattr(app_module, "prompt_llm", _boom, raising=True)

    r = client.post("/generate-task", json=coords)
    
    # It should NOT crash the app
    assert r.status_code == 200
    j = r.get_json()

    # The fallback string is expected (same as fallback in app.py)
    fallback_start = "Nice! That totally counts"
    assert isinstance(j["task"], str) and j["task"].startswith(fallback_start)
