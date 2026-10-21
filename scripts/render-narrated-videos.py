#!/usr/bin/env python3
"""Render the three handbook parts at 1.2x with narration and retimed subtitles."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEED = 1.2
PARTS = [
    ("part1-the-digital-universe", "part1-the-digital-universe"),
    ("part2-the-modern-frontend", "part2-the-modern-frontend"),
    ("part3-motion-and-magic", "part3-motion-and-magic"),
]


def run(args: list[str]) -> str:
    return subprocess.run(args, check=True, text=True, capture_output=True).stdout


def duration(path: Path) -> float:
    data = json.loads(run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "json", str(path),
    ]))
    return float(data["format"]["duration"])


def format_timestamp(milliseconds: int) -> str:
    hours, rem = divmod(milliseconds, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    seconds, millis = divmod(rem, 1_000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def retime_srt(source: Path, target: Path) -> None:
    text = source.read_text(encoding="utf-8-sig")
    timing = re.compile(r"(?m)^(\d{2}:\d{2}:\d{2},\d{3})\s+-->\s+(\d{2}:\d{2}:\d{2},\d{3})(.*)$")

    def scaled(match: re.Match[str]) -> str:
        def to_ms(value: str) -> int:
            h, m, rest = value.split(":")
            s, ms = rest.split(",")
            return ((int(h) * 60 + int(m)) * 60 + int(s)) * 1000 + int(ms)
        start = round(to_ms(match.group(1)) / SPEED)
        end = round(to_ms(match.group(2)) / SPEED)
        return f"{format_timestamp(start)} --> {format_timestamp(end)}{match.group(3)}"

    target.write_text(timing.sub(scaled, text), encoding="utf-8")


def render(stem: str) -> None:
    video = ROOT / f"{stem}.mp4"
    srt = ROOT / f"{stem}.srt"
    audio = ROOT / "audio" / "voiceovers" / f"{stem}.mp3"
    output = ROOT / f"{stem}-narrated-1.2x.mp4"
    scaled_srt = ROOT / f"{stem}-narrated-1.2x.srt"
    for required in (video, srt, audio):
        if not required.is_file():
            raise FileNotFoundError(required)

    target_duration = duration(video) / SPEED
    source_audio_duration = duration(audio)
    # atempo < 1 lengthens a shorter narration slightly, keeping it in sync with the clip.
    tempo = source_audio_duration / target_duration
    if not 0.5 <= tempo <= 2.0:
        raise ValueError(f"Audio/video duration mismatch for {stem}: atempo={tempo:.3f}")
    retime_srt(srt, scaled_srt)

    subprocess.run([
        "ffmpeg", "-hide_banner", "-y",
        "-i", str(video), "-i", str(audio), "-i", str(scaled_srt),
        "-map", "0:v:0", "-map", "1:a:0", "-map", "2:0",
        "-vf", f"setpts=PTS/{SPEED}",
        "-af", f"atempo={tempo:.8f},apad",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        "-c:s", "mov_text", "-metadata:s:s:0", "language=eng",
        "-movflags", "+faststart", "-t", f"{target_duration:.3f}", str(output),
    ], check=True)
    print(f"Rendered {output.name}: {target_duration:.2f}s picture; voice tempo filter {tempo:.4f}.")
    print(f"Retimed subtitles: {scaled_srt.name}")


if __name__ == "__main__":
    for source_stem, _ in PARTS:
        render(source_stem)
