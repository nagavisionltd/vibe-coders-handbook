#!/usr/bin/env python3
"""Join the three narrated 1.2x parts into a full handbook video."""
from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STEMS = [
    "part1-the-digital-universe",
    "part2-the-modern-frontend",
    "part3-motion-and-magic",
]
OUTPUT = ROOT / "vibe-coders-handbook-full-narrated-1.2x.mp4"
FULL_SRT = ROOT / "vibe-coders-handbook-full-narrated-1.2x.srt"
CHAPTERS_OUT = ROOT / "youtube-chapters-narrated-1.2x.txt"


def run(args: list[str]) -> str:
    return subprocess.run(args, check=True, text=True, capture_output=True).stdout


def duration_ms(path: Path) -> int:
    import json
    data = json.loads(run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "json", str(path),
    ]))
    return round(float(data["format"]["duration"]) * 1000)


def timestamp_ms(value: str) -> int:
    h, m, rest = value.split(":")
    s, ms = rest.split(",")
    return ((int(h) * 60 + int(m)) * 60 + int(s)) * 1000 + int(ms)


def format_srt(milliseconds: int) -> str:
    h, rem = divmod(milliseconds, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def combined_subtitles(paths: list[Path], offsets: list[int]) -> str:
    blocks: list[str] = []
    index = 1
    for path, offset in zip(paths, offsets):
        raw = path.read_text(encoding="utf-8-sig").strip()
        for block in re.split(r"\n\s*\n", raw):
            lines = block.splitlines()
            if len(lines) < 3:
                continue
            match = re.match(r"^(\d{2}:\d{2}:\d{2},\d{3})\s+-->\s+(\d{2}:\d{2}:\d{2},\d{3})(.*)$", lines[1])
            if not match:
                continue
            start = format_srt(timestamp_ms(match.group(1)) + offset)
            end = format_srt(timestamp_ms(match.group(2)) + offset)
            timing = f"{start} --> {end}{match.group(3)}"
            blocks.append("\n".join([str(index), timing, *lines[2:]]))
            index += 1
    return "\n\n".join(blocks) + "\n"


def retime_chapters(source: Path) -> str:
    lines: list[str] = []
    for line in source.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^(\d+):(\d{2})\s+(.+)$", line.strip())
        if not match:
            continue
        seconds = int(match.group(1)) * 60 + int(match.group(2))
        adjusted = round(seconds / 1.2)
        lines.append(f"{adjusted // 60}:{adjusted % 60:02d} {match.group(3)}")
    return "\n".join(lines) + "\n"


def main() -> None:
    videos = [ROOT / f"{stem}-narrated-1.2x.mp4" for stem in STEMS]
    srts = [ROOT / f"{stem}-narrated-1.2x.srt" for stem in STEMS]
    for path in [*videos, *srts, ROOT / "youtube-chapters.txt"]:
        if not path.is_file():
            raise FileNotFoundError(path)

    offsets: list[int] = []
    total = 0
    for video in videos:
        offsets.append(total)
        total += duration_ms(video)

    FULL_SRT.write_text(combined_subtitles(srts, offsets), encoding="utf-8")
    CHAPTERS_OUT.write_text(retime_chapters(ROOT / "youtube-chapters.txt"), encoding="utf-8")

    with tempfile.TemporaryDirectory(prefix="vibe-full-concat-") as temp_dir:
        concat_list = Path(temp_dir) / "parts.txt"
        concat_list.write_text("".join(f"file '{path.as_posix()}'\n" for path in videos), encoding="utf-8")
        subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "concat", "-safe", "0", "-i", str(concat_list),
            "-i", str(FULL_SRT),
            "-map", "0:v:0", "-map", "0:a:0", "-map", "1:0",
            "-c:v", "copy", "-c:a", "copy", "-c:s", "mov_text",
            "-metadata:s:s:0", "language=eng", "-movflags", "+faststart",
            "-t", f"{total / 1000:.3f}", str(OUTPUT),
        ], check=True)

    print(f"Assembled {OUTPUT.name}: {total / 1000:.3f}s from 3 processed parts.")
    print(f"Full subtitles: {FULL_SRT.name}")
    print(f"Retimed YouTube chapters: {CHAPTERS_OUT.name}")


if __name__ == "__main__":
    main()
