import argparse
import json
import math
import os
from pathlib import Path

import imageio_ffmpeg
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


def render_frame(config, frame_index):
    width = int(config.get("width", 1280))
    height = int(config.get("height", 720))
    fps = int(config.get("fps", 30))
    duration = float(config.get("duration_seconds", 12))
    t = frame_index / fps
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
    title = str(config.get("title", "THE BIG MONEY QUESTION")).upper()
    subtitle = str(config.get("subtitle", "Follow the numbers. Understand the pressure."))

    # Brand header.
    draw.rounded_rectangle((72, 58, 82, 84), radius=5, fill=(53, 215, 242, 255))
    draw.text((98, 58), channel, font=small, fill=(224, 237, 255, 235))
    draw.text((width - 230, 61), "FINANCIAL STORIES  /  01",
              font=label_font, fill=(145, 169, 202, 220))

    # Kinetic title entrance.
    title_alpha = int(255 * ease_out(t / 1.2))
    title_y = 190 + int((1 - ease_out(t / 1.2)) * 38)
    draw.text((74, title_y), title, font=title_font,
              fill=(245, 249, 255, title_alpha), stroke_width=1,
              stroke_fill=(53, 215, 242, min(90, title_alpha)))
    subtitle_alpha = int(230 * ease_out((t - 0.45) / 1.0))
    draw.text((78, title_y + 88), subtitle, font=subtitle_font,
              fill=(174, 193, 220, subtitle_alpha))

    # Animated chart panel.
    panel = (76, 405, width - 76, height - 72)
    draw.rounded_rectangle(panel, radius=24, fill=(12, 24, 44, 225),
                           outline=(77, 116, 160, 95), width=2)
    draw.text((108, 430), "COST PRESSURE INDEX", font=label_font,
              fill=(145, 169, 202, 255))
    chart = config.get("chart", [])
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

    return np.asarray(image, dtype=np.uint8)


def main():
    parser = argparse.ArgumentParser(description="Render a Money Under Pressure motion graphics video.")
    parser.add_argument("--project", default="renderer/sample_project.json")
    parser.add_argument("--output", default="output/money-under-pressure-demo.mp4")
    args = parser.parse_args()

    config = json.loads(Path(args.project).read_text(encoding="utf-8"))
    width = int(config.get("width", 1280))
    height = int(config.get("height", 720))
    fps = int(config.get("fps", 30))
    frames = int(float(config.get("duration_seconds", 12)) * fps)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)

    writer = imageio_ffmpeg.write_frames(
        args.output, (width, height), fps=fps, codec="libx264",
        pix_fmt_out="yuv420p",
        output_params=["-crf", "20", "-preset", "ultrafast", "-movflags", "+faststart"]
    )
    writer.send(None)
    try:
        for index in range(frames):
            writer.send(render_frame(config, index).tobytes())
    finally:
        writer.close()
    print(f"Rendered {frames} frames to {args.output}")


if __name__ == "__main__":
    main()
