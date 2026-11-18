import argparse
import asyncio
import subprocess
import json
import math
import os
from pathlib import Path

import imageio_ffmpeg
import edge_tts
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def load_font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def ease_out(value):
    value = max(0.0, min(1.0, value))
    return 1.0 - (1.0 - value) ** 3


def render_vertical_frame(config, frame_index):
    width, height = 720, 1280
    fps = int(config.get("fps", 30))
    duration = float(config.get("duration_seconds", 30))
    t = frame_index / fps
    scenes = config.get("scenes", [])
    scene_duration = duration / max(1, len(scenes))
    scene_index = min(len(scenes) - 1, int(t / scene_duration)) if scenes else 0
    scene = scenes[scene_index] if scenes else config
    local_t = max(0.0, t - scene_index * scene_duration)
    progress = min(1.0, local_t / scene_duration)

    y = np.linspace(0, 1, height, dtype=np.float32)[:, None, None]
    top = np.array([7, 13, 29], dtype=np.float32)[None, None, :]
    bottom = np.array([15, 25, 53], dtype=np.float32)[None, None, :]
    gradient = np.broadcast_to(top * (1 - y) + bottom * y, (height, width, 3)).copy()
    image = Image.fromarray(gradient.astype(np.uint8), "RGB")
    draw = ImageDraw.Draw(image, "RGBA")
    pulse = 0.5 + 0.5 * math.sin(t * 0.8)
    draw.ellipse((360, -160, 850, 330), fill=(34, 211, 238, int(20 + pulse * 18)))
    draw.ellipse((-260, 820, 280, 1380), fill=(139, 92, 246, 30))
    for x in range(0, width, 60):
        draw.line((x, 0, x, height), fill=(100, 160, 210, 12), width=1)
    for yy in range(0, height, 60):
        draw.line((0, yy, width, yy), fill=(100, 160, 210, 12), width=1)

    brand_font = load_font(18, True)
    title_font = load_font(48, True)
    subtitle_font = load_font(27)
    label_font = load_font(17, True)
    number_font = load_font(25, True)
    channel = str(config.get("channel", "MONEY UNDER PRESSURE")).upper()
    title = str(scene.get("title", config.get("title", "MONEY UNDER PRESSURE"))).upper()
    subtitle = str(scene.get("subtitle", config.get("subtitle", "")))
    draw.rounded_rectangle((44, 54, 56, 84), radius=5, fill=(53, 215, 242, 255))
    draw.text((72, 55), channel, font=brand_font, fill=(224, 237, 255, 245))
    draw.text((44, 160), "THE MONEY STORY", font=label_font, fill=(53, 215, 242, 255))

    def wrapped(text, font, max_width):
        words = text.split()
        lines, line = [], ""
        for word in words:
            candidate = (line + " " + word).strip()
            if draw.textbbox((0, 0), candidate, font=font)[2] <= max_width:
                line = candidate
            else:
                if line:
                    lines.append(line)
                line = word
        if line:
            lines.append(line)
        return lines[:5]

    title_lines = wrapped(title, title_font, 625)
    title_y = 250 + int((1 - ease_out(local_t / 0.8)) * 35)
    for line in title_lines:
        draw.text((44, title_y), line, font=title_font, fill=(245, 249, 255, int(255 * ease_out(local_t / 0.8))))
        title_y += 62
    subtitle_y = title_y + 24
    for line in wrapped(subtitle, subtitle_font, 620):
        draw.text((48, subtitle_y), line, font=subtitle_font, fill=(174, 193, 220, int(235 * ease_out((local_t - 0.2) / 0.8))))
        subtitle_y += 39

    panel_top = 790
    draw.rounded_rectangle((36, panel_top, 684, 1160), radius=28, fill=(12, 24, 44, 230), outline=(77, 116, 160, 110), width=2)
    draw.text((66, panel_top + 34), "FOLLOW THE NUMBERS", font=label_font, fill=(145, 169, 202, 255))
    chart = scene.get("chart", config.get("chart", []))
    if chart:
        values = [float(item.get("value", 0)) for item in chart[:4]]
        labels = [str(item.get("label", ""))[:12] for item in chart[:4]]
    else:
        values, labels = [35, 58, 76, 92], ["COST", "DEBT", "PRICE", "PRESSURE"]
    max_value = max(values) or 1
    base_y, chart_h = 1080, 190
    bar_w, gap = 105, 34
    for i, value in enumerate(values):
        local = max(0.0, min(1.0, progress * len(values) - i + 0.15))
        bar_h = chart_h * value / max_value * ease_out(local)
        x0 = 68 + i * (bar_w + gap)
        draw.rounded_rectangle((x0, base_y - bar_h, x0 + bar_w, base_y), radius=10, fill=(42, 190, 226, 225))
        draw.text((x0, base_y + 18), labels[i], font=label_font, fill=(160, 180, 207, 255))
    draw.text((44, 1190), "MONEY UNDER PRESSURE  •  FOLLOW FOR MORE", font=label_font, fill=(53, 215, 242, 230))
    return np.asarray(image, dtype=np.uint8)


def render_frame(config, frame_index):
    if config.get("vertical", False):
        return render_vertical_frame(config, frame_index)
    width = int(config.get("width", 1280))
    height = int(config.get("height", 720))
    fps = int(config.get("fps", 30))
    duration = float(config.get("duration_seconds", 12))
    t = frame_index / fps
    scenes = config.get("scenes", [])
    if scenes:
        scene_duration = duration / len(scenes)
        scene_index = min(len(scenes) - 1, int(t / scene_duration))
        scene_start = scene_index * scene_duration
        scene = scenes[scene_index]
        local_t = max(0.0, t - scene_start)
        progress = min(1.0, local_t / scene_duration)
    else:
        scene_index = 0
        local_t = t
        scene = config
        progress = min(1.0, t / duration)

    y = np.linspace(0, 1, height, dtype=np.float32)[:, None, None]
    top = np.array([7, 13, 29], dtype=np.float32)[None, None, :]
    bottom = np.array([15, 25, 53], dtype=np.float32)[None, None, :]
    gradient = np.broadcast_to(top * (1 - y) + bottom * y, (height, width, 3)).copy()
    image = Image.fromarray(gradient.astype(np.uint8), "RGB")
    draw = ImageDraw.Draw(image, "RGBA")

    # Ambient cyan and violet light fields.
    pulse = 0.5 + 0.5 * math.sin(t * 0.8)
    draw.ellipse((width * 0.62, -height * 0.55, width * 1.15, height * 0.55),
                 fill=(34, 211, 238, int(15 + pulse * 12)))
    draw.ellipse((-width * 0.35, height * 0.45, width * 0.45, height * 1.3),
                 fill=(139, 92, 246, 24))

    # Subtle technical grid.
    for x in range(0, width, 64):
        draw.line((x, 0, x, height), fill=(100, 160, 210, 13), width=1)
    for yy in range(0, height, 64):
        draw.line((0, yy, width, yy), fill=(100, 160, 210, 13), width=1)

    small = load_font(18, True)
    title_font = load_font(62, True)
    subtitle_font = load_font(27)
    label_font = load_font(16, True)
    number_font = load_font(22, True)

    channel = str(config.get("channel", "MONEY UNDER PRESSURE")).upper()
    title = str(scene.get("title", config.get("title", "THE BIG MONEY QUESTION"))).upper()
    subtitle = str(scene.get("subtitle", config.get("subtitle", "Follow the numbers. Understand the pressure.")))

    # Brand header.
    draw.rounded_rectangle((72, 58, 82, 84), radius=5, fill=(53, 215, 242, 255))
    draw.text((98, 58), channel, font=small, fill=(224, 237, 255, 235))
    draw.text((width - 230, 61), "FINANCIAL STORIES  /  01",
              font=label_font, fill=(145, 169, 202, 220))

    # Kinetic title entrance.
    title_alpha = int(255 * ease_out(local_t / 0.85))
    title_y = 190 + int((1 - ease_out(local_t / 0.85)) * 38)
    draw.text((74, title_y), title, font=title_font,
              fill=(245, 249, 255, title_alpha), stroke_width=1,
              stroke_fill=(53, 215, 242, min(90, title_alpha)))
    subtitle_alpha = int(230 * ease_out((local_t - 0.25) / 0.75))
    draw.text((78, title_y + 88), subtitle, font=subtitle_font,
              fill=(174, 193, 220, subtitle_alpha))

    # Animated chart panel.
    panel = (76, 405, width - 76, height - 72)
    draw.rounded_rectangle(panel, radius=24, fill=(12, 24, 44, 225),
                           outline=(77, 116, 160, 95), width=2)
    draw.text((108, 430), "COST PRESSURE INDEX", font=label_font,
              fill=(145, 169, 202, 255))
    chart = scene.get("chart", config.get("chart", []))
    if chart:
        values = [float(item.get("value", 0)) for item in chart]
        labels = [str(item.get("label", "")) for item in chart]
        max_value = max(values) or 1
        chart_left, chart_top = 130, 500
        chart_width, chart_height = width - 270, 130
        gap = 22
        bar_width = (chart_width - gap * (len(values) - 1)) / len(values)
        visible = min(len(values), max(1, int(progress * len(values)) + 1))
        for i, value in enumerate(values[:visible]):
            local = max(0.0, min(1.0, (progress * len(values) - i) + 0.15))
            bar_h = chart_height * (value / max_value) * ease_out(local)
            x0 = chart_left + i * (bar_width + gap)
            y0 = chart_top + chart_height - bar_h
            draw.rounded_rectangle((x0, y0, x0 + bar_width, chart_top + chart_height),
                                   radius=8, fill=(42, 190, 226, 220))
            draw.text((x0, chart_top + chart_height + 12), labels[i],
                      font=label_font, fill=(160, 180, 207, 255))
        draw.text((width - 190, 430), f"{int(values[min(len(values)-1, int(progress*len(values)))])}%",
                  font=number_font, fill=(53, 215, 242, 255))

    # Moving scan line adds a restrained cinematic accent.
    scan_x = int((t * 110) % (width + 200)) - 100
    draw.line((scan_x, 120, scan_x + 110, height - 100),
              fill=(53, 215, 242, 24), width=3)

    # Brief cinematic fade at each scene boundary prevents hard visual cuts.
    if scenes and scene_index > 0 and local_t < 0.32:
        fade_alpha = int(150 * (1.0 - ease_out(local_t / 0.32)))
        fade = Image.new("RGBA", (width, height), (3, 8, 20, fade_alpha))
        image = Image.alpha_composite(image.convert("RGBA"), fade).convert("RGB")

    return np.asarray(image, dtype=np.uint8)


async def create_narration(text, voice, output_path):
    # Prefer the natural neural voice, but never let a third-party TTS outage
    # prevent a video from rendering. Fall back to local offline speech.
    neural_path = output_path.with_suffix(".mp3")
    try:
        if os.getenv("MUP_FORCE_OFFLINE_TTS") == "1":
            raise RuntimeError("Offline narration explicitly selected for integration testing.")
        communicate = edge_tts.Communicate(text=text, voice=voice)
        await asyncio.wait_for(communicate.save(str(neural_path)), timeout=20)
        if neural_path.is_file() and neural_path.stat().st_size > 1024:
            print("Narration generated with neural voice.")
            return neural_path
        raise RuntimeError("Neural TTS returned an empty audio file.")
    except Exception as exc:
        neural_path.unlink(missing_ok=True)
        print(f"Neural TTS unavailable ({type(exc).__name__}); using offline fallback.")
        text_path = output_path.with_suffix(".txt")
        text_path.write_text(text, encoding="utf-8")
        try:
            result = subprocess.run(
                ["espeak-ng", "-v", "en-us", "-s", "155", "-f",
                 str(text_path), "-w", str(output_path.with_suffix(".wav"))],
                capture_output=True, text=True, check=False, timeout=30
            )
            if result.returncode != 0:
                raise RuntimeError("Offline speech engine failed: " + (result.stderr or result.stdout)[-1200:])
            wav_path = output_path.with_suffix(".wav")
            if not wav_path.is_file() or wav_path.stat().st_size <= 1024:
                raise RuntimeError("Offline speech engine produced no audio.")
            print("Narration generated with offline English fallback voice.")
            return wav_path
        finally:
            text_path.unlink(missing_ok=True)


def media_duration(path, ffmpeg_exe):
    probe = subprocess.run(
        [ffmpeg_exe, "-nostdin", "-hide_banner", "-v", "info", "-i", str(path), "-f", "null", "-"],
        capture_output=True, text=True, check=False, timeout=30
    )
    import re
    match = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", probe.stderr)
    if not match:
        raise RuntimeError("Could not determine generated narration duration.")
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def main():
    parser = argparse.ArgumentParser(description="Render a Money Under Pressure motion graphics video.")
    parser.add_argument("--project", default="renderer/sample_project.json")
    parser.add_argument("--output", default="output/money-under-pressure-demo.mp4")
    args = parser.parse_args()

    config = json.loads(Path(args.project).read_text(encoding="utf-8"))
    width = int(config.get("width", 1280))
    height = int(config.get("height", 720))
    fps = int(config.get("fps", 30))
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    script = str(config.get("script", "")).strip()
    narration_enabled = bool(config.get("narration_enabled", True)) and bool(script)
    audio_base_path = output_path.with_suffix(".narration")
    silent_path = output_path.with_name(output_path.stem + ".silent.mp4")
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    if narration_enabled:
        voice = str(config.get("voice", "en-US-AriaNeural"))
        print(f"Generating narration with voice {voice}", flush=True)
        audio_path = asyncio.run(create_narration(script, voice, audio_base_path))
        audio_seconds = media_duration(audio_path, ffmpeg_exe)
        config["duration_seconds"] = min(900, max(float(config.get("duration_seconds", 12)), audio_seconds + 0.8))
        if audio_seconds + 0.8 > 900:
            raise ValueError("Narration exceeds the 15-minute maximum. Shorten the script.")
        print(f"Narration duration: {audio_seconds:.1f}s", flush=True)

    frames = int(float(config.get("duration_seconds", 12)) * fps)
    video_target = str(silent_path if narration_enabled else output_path)
    writer = imageio_ffmpeg.write_frames(
        video_target, (width, height), fps=fps, codec="libx264",
        pix_fmt_out="yuv420p",
        output_params=["-crf", "20", "-preset", "ultrafast", "-movflags", "+faststart"]
    )
    writer.send(None)
    try:
        for index in range(frames):
            writer.send(render_frame(config, index).tobytes())
    finally:
        writer.close()
    if narration_enabled:
        mux = subprocess.run(
            [ffmpeg_exe, "-y", "-i", str(silent_path), "-i", str(audio_path),
             "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
             "-c:a", "aac", "-b:a", "192k", "-af", "apad", "-shortest",
             "-movflags", "+faststart", str(output_path)],
            capture_output=True, text=True, check=False, timeout=90
        )
        if mux.returncode != 0:
            raise RuntimeError("Could not add narration to MP4: " + mux.stderr[-1200:])
        silent_path.unlink(missing_ok=True)
        audio_path.unlink(missing_ok=True)
    print(f"Rendered {frames} frames to {args.output}", flush=True)


if __name__ == "__main__":
    main()
