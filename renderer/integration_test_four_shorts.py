#!/usr/bin/env python3
"""Exercise the real API render_job path and render all four narrated vertical Shorts."""

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("STUDIO_API_TOKEN", "ci-four-shorts-token")

import imageio_ffmpeg
from fastapi.testclient import TestClient
from renderer import api


OUTPUT_DIR = ROOT / "output" / "four-shorts-integration"
JOB_ID = "ci-four-shorts-integration"
TOKEN = os.environ["STUDIO_API_TOKEN"]

SCRIPT = (
    "Inflation raises the price of everyday essentials. "
    "Paychecks often struggle to keep pace with rising costs. "
    "Families then spend more on housing, food, and transport. "
    "Small budget gaps can become serious financial pressure. "
    "Credit cards may cover the difference for a while. "
    "But interest charges make each borrowed dollar more expensive. "
    "Tracking spending reveals where money is disappearing. "
    "Planning ahead can help households regain some control."
)


def verify_mp4(path: Path, portrait: bool = False) -> float:
    if not path.is_file() or path.stat().st_size <= 1024:
        raise AssertionError(f"Missing or empty MP4: {path}")

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    decode = subprocess.run(
        [
            ffmpeg, "-nostdin", "-hide_banner", "-v", "error", "-i", str(path),
            "-map", "0:v:0", "-map", "0:a:0", "-f", "null", "-"
        ],
        capture_output=True, text=True, timeout=60
    )
    if decode.returncode != 0:
        raise AssertionError(f"Video/audio decode failed for {path.name}: {decode.stderr[-1500:]}")

    probe = subprocess.run(
        [ffmpeg, "-nostdin", "-hide_banner", "-i", str(path), "-f", "null", "-"],
        capture_output=True, text=True, timeout=30
    )
    if probe.returncode != 0:
        raise AssertionError(f"FFmpeg probe failed for {path.name}: {probe.stderr[-1500:]}")
    if "Audio:" not in probe.stderr or "Video:" not in probe.stderr:
        raise AssertionError(f"MP4 must contain video and narration audio: {path.name}")
    if portrait and "720x1280" not in probe.stderr:
        raise AssertionError(f"Short is not 720x1280 portrait: {path.name}")

    match = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", probe.stderr)
    if not match:
        raise AssertionError(f"Could not read duration for {path.name}")
    hours, minutes, seconds = match.groups()
    duration = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    if portrait and duration > 180.5:
        raise AssertionError(f"Short exceeds the 3-minute limit: {duration:.1f}s")
    return duration


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    api.OUTPUT_DIR = OUTPUT_DIR
    api.API_TOKEN = TOKEN
    api.jobs.pop(JOB_ID, None)
    for old_file in OUTPUT_DIR.glob(f"{JOB_ID}*"):
        if old_file.is_file():
            old_file.unlink()

    payload = {
        "title": "Four Shorts Integration Test",
        "subtitle": "A real API-path render test",
        "channel": "MONEY UNDER PRESSURE",
        "duration_seconds": 5,
        "fps": 24,
        "narration_enabled": True,
        "voice": "en-US-AriaNeural",
        "script": SCRIPT,
    }

    client = TestClient(api.app)
    headers = {"Authorization": f"Bearer {TOKEN}"}
    created = client.post("/v1/renders", json=payload, headers=headers)
    if created.status_code != 202:
        raise AssertionError(f"Render API did not accept the project: {created.status_code} {created.text}")
    job_id = created.json()["job_id"]

    status_response = client.get(f"/v1/renders/{job_id}", headers=headers)
    if status_response.status_code != 200:
        raise AssertionError(f"Could not retrieve completed render status: {status_response.text}")
    job = status_response.json()
    if job.get("status") != "completed":
        raise AssertionError(f"Long render failed: {job.get('error', job)}")
    if job.get("shorts_error"):
        raise AssertionError(f"Short generation reported an error: {job['shorts_error']}")

    shorts = job.get("shorts", [])
    if len(shorts) != 4 or [item.get("index") for item in shorts] != [1, 2, 3, 4]:
        raise AssertionError(f"Expected four ordered Shorts, got: {shorts}")

    long_path = OUTPUT_DIR / f"{job_id}.mp4"
    long_duration = verify_mp4(long_path)
    long_response = client.get(f"/v1/renders/{job_id}/download", headers=headers)
    if long_response.status_code != 200 or long_response.content != long_path.read_bytes():
        raise AssertionError("Authenticated long-video HTTP download did not match the rendered MP4.")
    print(f"Verified narrated long-video API output: {long_duration:.1f}s")

    for item in shorts:
        index = item["index"]
        path = OUTPUT_DIR / item["filename"]
        duration = verify_mp4(path, portrait=True)
        response = client.get(
            f"/v1/renders/{job_id}/shorts/{index}/download",
            headers=headers,
        )
        if response.status_code != 200 or response.content != path.read_bytes():
            raise AssertionError(f"Authenticated HTTP download failed for Short {index}.")
        print(
            f"Verified Short {index}/4: {duration:.1f}s, 720x1280, "
            "video and narration audio decode, authenticated HTTP download."
        )

    print("All four real narrated Shorts passed end-to-end HTTP API render and download checks.")


if __name__ == "__main__":
    main()
