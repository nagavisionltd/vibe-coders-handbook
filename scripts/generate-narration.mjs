#!/usr/bin/env node
import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";

const repoRoot = process.cwd();
const voiceId = process.env.ELEVENLABS_VOICE_ID || "JBFqnCBsd6RMkjVDRZzb"; // George — Warm, Captivating Storyteller
const modelId = process.env.ELEVENLABS_MODEL_ID || "eleven_multilingual_v2";
const outputFormat = process.env.ELEVENLABS_OUTPUT_FORMAT || "mp3_44100_128";
const defaultSrtFiles = [
  "part1-the-digital-universe.srt",
  "part2-the-modern-frontend.srt",
  "part3-motion-and-magic.srt",
];
const srtFiles = process.argv.slice(2).filter((arg) => !arg.startsWith("--"));
const inputs = srtFiles.length ? srtFiles : defaultSrtFiles;
const dryRun = process.argv.includes("--dry-run");

function srtToText(srt) {
  return srt
    .replace(/^\uFEFF/, "")
    .replace(/\r/g, "")
    .split(/\n\s*\n/)
    .map((block) => block.split("\n").slice(2).join(" ").trim())
    .filter(Boolean)
    .join(" ")
    .replace(/\s+/g, " ")
    .replace(/\bWeb\s+([123])\.\s*0\b/gi, "Web $1 point zero")
    .replace(/\bNext\.\s*js\b/gi, "Next.js")
    .replace(/\bAnime\.\s*js\b/gi, "Anime.js")
    .replace(/\bA\s+I\b/g, "AI")
    .trim();
}

if (!process.env.ELEVENLABS_API_KEY && !dryRun) {
  console.error("ELEVENLABS_API_KEY is not set. Set it in your shell environment; never put it in source code.");
  process.exit(1);
}

const prepared = [];
for (const input of inputs) {
  const srtPath = path.resolve(repoRoot, input);
  const srt = await readFile(srtPath, "utf8");
  const text = srtToText(srt);
  if (!text) throw new Error(`No subtitle text found in ${srtPath}`);
  prepared.push({ input: srtPath, text, output: path.resolve(repoRoot, "audio", "voiceovers", `${path.basename(input, path.extname(input))}.mp3`) });
}

const totalCharacters = prepared.reduce((sum, item) => sum + item.text.length, 0);
console.log(`Prepared ${prepared.length} narration track(s), ${totalCharacters} characters total.`);
for (const item of prepared) console.log(`${path.relative(repoRoot, item.input)} -> ${path.relative(repoRoot, item.output)} (${item.text.length} chars)`);
if (dryRun) process.exit(0);

const client = new ElevenLabsClient();
await mkdir(path.dirname(prepared[0].output), { recursive: true });
for (const item of prepared) {
  console.log(`Generating ${path.basename(item.output)}...`);
  const audio = await client.textToSpeech.convert(voiceId, {
    text: item.text,
    modelId,
    outputFormat,
    voiceSettings: {
      stability: 0.58,
      similarityBoost: 0.8,
      style: 0.15,
      speed: 1.15,
      useSpeakerBoost: true,
    },
  });
  const chunks = [];
  const reader = audio.getReader();
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(Buffer.from(value));
  }
  await writeFile(item.output, Buffer.concat(chunks));
  console.log(`Saved ${path.relative(repoRoot, item.output)}`);
}
