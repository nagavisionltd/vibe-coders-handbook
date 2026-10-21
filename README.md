# Vibe Coder's Handbook

A visual guide to commanding AI and modern development systems.

## Narration generation

This repository includes an ElevenLabs SDK workflow that turns the part subtitle files into spoken narration. It uses the account voice **George — Warm, Captivating Storyteller** by default, at a moderately brisk pace suitable for the 1.2× video edits.

Requirements: Node.js 20+, FFmpeg/ffprobe for video rendering, and an ElevenLabs API key supplied through the `ELEVENLABS_API_KEY` environment variable. Never put API keys in this repository. Optional environment variables: `ELEVENLABS_VOICE_ID` (voice override), `ELEVENLABS_MODEL_ID`, and `ELEVENLABS_OUTPUT_FORMAT`.

```bash
npm install
npm run narrate -- --dry-run
npm run narrate
npm run render
```

The script reads `part1-the-digital-universe.srt`, `part2-the-modern-frontend.srt`, and `part3-motion-and-magic.srt` by default, and writes MP3 narration to `audio/voiceovers/`. You can pass specific SRT paths as arguments. Generation uses ElevenLabs credits. `scripts/render-narrated-videos.py` creates 1.2× MP4s with retimed subtitles and the matching narration audio.

## Video exports

The original silent MP4s are retained unchanged. The `-narrated-1.2x.mp4` exports use 1.2× picture speed, the matching narration audio, and retimed embedded subtitles. Corresponding retimed SRT sidecars are included alongside the MP4s.
