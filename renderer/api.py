import json
import os
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
    scenes: list[Scene] = Field(default_factory=list, max_length=20)


class RenderRequest(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    subtitle: str = Field(default="", max_length=180)
    channel: str = Field(default="MONEY UNDER PRESSURE", max_length=60)
    duration_seconds: int = Field(default=12, ge=5, le=60)
    fps: int = Field(default=30, ge=24, le=30)
    chart: list[ChartPoint] = Field(default_factory=list, max_length=12)


def require_token(authorization: str | None):
    if not API_TOKEN:
        raise HTTPException(status_code=503, detail="Render API is not configured with STUDIO_API_TOKEN.")
    expected = f"Bearer {API_TOKEN}"
    if not authorization or not secrets.compare_digest(authorization, expected):
        raise HTTPException(status_code=401, detail="A valid bearer token is required.")


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
            check=True, cwd=str(ROOT), timeout=900
        )
        with lock:
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["download_path"] = str(output_path)
    except Exception as exc:
        with lock:
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
