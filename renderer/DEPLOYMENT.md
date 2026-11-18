# Deploy the render server

The app's rendering API is packaged as a Docker web service. This repository includes a Render Blueprint at the root.

## Deploy

1. Sign in to Render and choose **New → Blueprint**.
2. Connect the GitHub repository `czz495m8zv-code/money--under-presssure-studio`.
3. Review the `money-under-pressure-renderer` service and deploy it.
4. Render generates `STUDIO_API_TOKEN` automatically. Keep this value private.
5. Once the service is live, its health URL should return JSON at `https://YOUR-SERVICE.onrender.com/health`.

## Important limitations of the free prototype

- Free web services may sleep when idle and take time to wake.
- The current API stores job status in process memory. A restart clears job history.
- The generated MP4 is on ephemeral service storage. Download it before the service restarts.
- This is a prototype for testing, not yet a production video platform. A persistent job queue, durable object storage, user accounts, quotas and stronger operational monitoring are still required.

Do not put the API token in a public repository, screenshot or shared message. The Android app already includes encrypted token storage, server URL settings, render-job polling and MP4 download. After deployment, enter the HTTPS service URL and generated token in the app's Settings screen. The current renderer can produce up to 15 minutes of video and optionally synthesizes English narration through the external Edge TTS service; this requires outbound internet access.

**Long-form caution:** the free hosting tier is suitable only for a small proof of concept. A 8–15 minute render can exceed free CPU, memory, request or service-lifetime limits. Do not rely on a free instance for dependable long-form production. Before public or regular use, move to a suitable persistent worker/server and object storage, and implement a durable queue.
