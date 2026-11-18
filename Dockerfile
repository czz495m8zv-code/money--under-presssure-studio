FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /studio
COPY renderer/requirements.txt /studio/renderer/requirements.txt
RUN apt-get update && apt-get install -y --no-install-recommends espeak-ng \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r /studio/renderer/requirements.txt
COPY renderer /studio/renderer

RUN mkdir -p /studio/output/jobs
EXPOSE 8000
CMD ["uvicorn", "renderer.api:app", "--host", "0.0.0.0", "--port", "8000"]
