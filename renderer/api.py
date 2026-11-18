import json
import os
import re
import secrets
import subprocess
import sys
import threading
import uuid
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "output" / "jobs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
API_TOKEN = os.environ.get("STUDIO_API_TOKEN", "")
app = FastAPI(title="Money Under Pressure Render API", version="0.1.0")
jobs: dict[str, dict[str, Any]] = {}
lock = threading.Lock()


class ChartPoint(BaseModel):
    label: str = Field(max_length=32)
    value: float = Field(ge=0, le=100000)


class Scene(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    subtitle: str = Field(default="", max_length=180)
    chart: list[ChartPoint] = Field(default_factory=list, max_length=12)


class RenderRequest(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    subtitle: str = Field(default="", max_length=180)
    channel: str = Field(default="MONEY UNDER PRESSURE", max_length=60)
    duration_seconds: int = Field(default=12, ge=5, le=900)
    fps: int = Field(default=30, ge=24, le=30)
    chart: list[ChartPoint] = Field(default_factory=list, max_length=12)
    scenes: list[Scene] = Field(default_factory=list, max_length=20)
    script: str = Field(default="", max_length=30000)
    narration_enabled: bool = True
    voice: str = Field(default="en-US-AriaNeural", max_length=80)



def script_to_scenes(script: str) -> list[dict[str, Any]]:
    # Turn script paragraphs/sentences into readable visual beats.
    if not script.strip():
        return []
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", script) if part.strip()]
    if not sentences:
        return []
    group_size = max(1, (len(sentences) + 19) // 20)
    beats = [" ".join(sentences[i:i + group_size]) for i in range(0, len(sentences), group_size)][:20]
    scenes = []
    for index, beat in enumerate(beats):
        words = beat.split()
        title = " ".join(words[:7]).strip(" .,!?:;")
        subtitle = " ".join(words[7:24]).strip()
        scenes.append({
            "title": title[:100] or f"KEY POINT {index + 1}",
            "subtitle": subtitle[:180],
            "chart": []
        })
    return scenes

def require_token(authorization: str | None):
    if not API_TOKEN:
        raise HTTPException(status_code=503, detail="Render API is not configured with STUDIO_API_TOKEN.")
    expected = f"Bearer {API_TOKEN}"
    if not authorization or not secrets.compare_digest(authorization, expected):
        raise HTTPException(status_code=401, detail="A valid bearer token is required.")


def split_script_for_shorts(script: str, count: int = 4) -> list[str]:
    words = script.split()
    if not words:
        return []
    count = min(count, len(words))
    base, extra = divmod(len(words), count)
    chunks = []
    offset = 0
    for index in range(count):
        size = base + (1 if index < extra else 0)
        chunks.append(" ".join(words[offset:offset + size]))
        offset += size
    return chunks


def render_job(job_id: str, payload: dict[str, Any]):
    project_path = OUTPUT_DIR / f"{job_id}.json"
    output_path = OUTPUT_DIR / f"{job_id}.mp4"
    project_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    with lock:
        jobs[job_id]["status"] = "rendering"
    try:
        subprocess.run(
            [sys.executable, str(ROOT / "renderer" / "render_video.py"),
             "--project", str(project_path), "--output", str(output_path)],
            check=True, cwd=str(ROOT), timeout=3600
        )
        shorts = []
        script = str(payload.get("script", "")).strip()
        if script:
            with lock:
                jobs[job_id]["status"] = "creating_shorts"
            for index, short_script in enumerate(split_script_for_shorts(script, 4), start=1):
                short_id = f"{job_id}-short-{index}"
                short_project = OUTPUT_DIR / f"{short_id}.json"
                short_output = OUTPUT_DIR / f"{short_id}.mp4"
                short_title = " ".join(short_script.split()[:7]).strip(" .,!?:;") or f"Money Short {index}"
                short_payload = {
                    "title": short_title[:100],
                    "subtitle": "A key moment from the full Money Under Pressure story",
                    "channel": payload.get("channel", "MONEY UNDER PRESSURE"),
                    "duration_seconds": 30,
                    "fps": 30,
                    "width": 720,
                    "height": 1280,
                    "vertical": True,
                    "narration_enabled": bool(payload.get("narration_enabled", True)),
                    "voice": payload.get("voice", "en-US-AriaNeural"),
                    "script": short_script,
                    "scenes": script_to_scenes(short_script)
                }
                short_project.write_text(json.dumps(short_payload, ensure_ascii=False), encoding="utf-8")
                subprocess.run(
                    [sys.executable, str(ROOT / "renderer" / "render_video.py"),
                     "--project", str(short_project), "--output", str(short_output)],
                    check=True, cwd=str(ROOT), timeout=900
                )
                shorts.append({"index": index, "filename": short_output.name, "title": short_title})
                with lock:
                    jobs[job_id]["shorts"] = list(shorts)
        with lock:
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["download_path"] = str(output_path)
            jobs[job_id]["shorts"] = shorts
    except Exception as exc:
        with lock:
            if output_path.is_file():
                jobs[job_id]["status"] = "completed"
                jobs[job_id]["download_path"] = str(output_path)
                jobs[job_id]["shorts_error"] = str(exc)[:500]
            else:
                jobs[job_id]["status"] = "failed"
                jobs[job_id]["error"] = str(exc)[:500]


@app.get("/health")
def health():
    return {"service": "money-under-pressure-renderer", "status": "ok", "version": "0.1.0"}


@app.post("/v1/renders", status_code=202)
def create_render(request: RenderRequest, background_tasks: BackgroundTasks,
                  authorization: str | None = Header(default=None)):
    require_token(authorization)
    job_id = uuid.uuid4().hex
    payload = request.model_dump()
    if payload["script"].strip() and payload["duration_seconds"] <= 12:
        estimated = int(len(payload["script"].split()) / 2.35) + 3
        payload["duration_seconds"] = min(900, max(12, estimated))
    if not payload["scenes"] and payload["script"].strip():
        payload["scenes"] = script_to_scenes(payload["script"])
    with lock:
        jobs[job_id] = {"id": job_id, "status": "queued"}
    background_tasks.add_task(render_job, job_id, payload)
    return {"job_id": job_id, "status": "queued"}


@app.get("/v1/renders/{job_id}")
def render_status(job_id: str, authorization: str | None = Header(default=None)):
    require_token(authorization)
    with lock:
        job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Render job not found.")
    return {key: value for key, value in job.items() if key != "download_path"}


@app.get("/v1/renders/{job_id}/shorts/{short_index}/download")
def download_short(job_id: str, short_index: int, authorization: str | None = Header(default=None)):
    require_token(authorization)
    with lock:
        job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Render job not found.")
    shorts = job.get("shorts", [])
    match = next((item for item in shorts if item.get("index") == short_index), None)
    if not match:
        raise HTTPException(status_code=404, detail="This Short is not available.")
    path = OUTPUT_DIR / match["filename"]
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Short video file is missing.")
    return FileResponse(path, media_type="video/mp4", filename=f"money-under-pressure-short-{short_index}.mp4")


@app.get("/v1/renders/{job_id}/download")
def download_render(job_id: str, authorization: str | None = Header(default=None)):
    require_token(authorization)
    with lock:
        job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Render job not found.")
    if job.get("status") != "completed":
        raise HTTPException(status_code=409, detail="The video is not ready yet.")
    path = Path(job["download_path"])
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Rendered video file is missing.")
    return FileResponse(path, media_type="video/mp4", filename=f"money-under-pressure-{job_id}.mp4")
