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
- The current renderer creates a visual demo from title, subtitle and chart data. Voice-over, research, stock footage, full scene authoring and production-grade queueing are later milestones.
