# Render engine and API

This service accepts a video project, renders an MP4 with the Money Under Pressure motion-graphics renderer, and exposes job status and download endpoints.

## Run with Docker

Set a long random token in your shell as `STUDIO_API_TOKEN`, then run:

```bash
docker compose up --build -d
```

Health check: `GET /health`

## API

All `/v1` endpoints require:

`Authorization: Bearer YOUR_STUDIO_API_TOKEN`

Create a render:

```http
POST /v1/renders
Content-Type: application/json
Authorization: Bearer YOUR_STUDIO_API_TOKEN

{
  "title": "THE COST OF LIVING",
  "subtitle": "Why your money feels like it buys less",
  "duration_seconds": 12,
  "fps": 30,
  "chart": [
    {"label": "2019", "value": 42},
    {"label": "2024", "value": 91}
  ]
}
```

The response returns a `job_id`. Poll `GET /v1/renders/{job_id}` until status is `completed`, then fetch `GET /v1/renders/{job_id}/download`.

## Notes

- This is an early single-process prototype. Job state is held in memory and is lost if the service restarts.
- Use HTTPS and a private network or trusted hosting environment before connecting a public mobile app.
- Set a unique, high-entropy API token. Do not commit it to Git.
- The renderer supports up to 15 minutes per job and can generate an English neural voice-over from a supplied script using the Edge TTS service. Long scripts are grouped into up to 20 visual beats so the full narration is retained. Narration requires outbound internet access and may be unavailable if that external service changes or blocks requests.
- Script duration is estimated automatically when the app sends its default short duration. Explicit duration values are accepted up to 900 seconds.
- This is still an early single-process prototype: no built-in research, original scriptwriting, stock footage, persistent queue/storage, user accounts, quotas, or production-grade job recovery.

- Every render with a narration script also creates four separate vertical 9:16 MP4 Shorts, each with its own excerpt and generated narration. The API exposes each Short through an authenticated download endpoint; the Android app downloads the long video and all generated Shorts into Movies/Money Under Pressure. Shorts are extracted from the supplied script, not automatically rewritten or independently fact-checked.
