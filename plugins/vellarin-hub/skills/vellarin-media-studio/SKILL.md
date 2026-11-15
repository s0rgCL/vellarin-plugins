---
name: vellarin-media-studio
description: Make short vertical videos (Instagram Reels, TikTok) of a realistic fictional person speaking a script, with subtitles, using the user's own image and video generation connector (for example Buzzy) and Vellarin Hub for budget, approval and the record. Use when the user asks for a reel, a talking-head video, a batch of brand videos, or captions for them, and the Vellarin MCP server (tools vellarin_media_checkpoint, vellarin_media_log, vellarin_media_status) is available.
---

# Vellarin Media Studio

You make the video with the **user's own generation connector** (their account, their credits; Buzzy is the one this recipe was
measured with). Vellarin Hub does not generate anything and holds no provider key. Hub is where the owner set a budget, where a costly
or risky step waits for their approval, and where the record of every step is kept. `scripts/reel.py` (in this skill) plans, checks
and assembles; it runs on the user's computer or in the provider's sandbox and needs no key.

If no generation connector is available, say so and stop: ask the user to connect one in their assistant. Do not look for another way.

## The three Hub tools

- `vellarin_media_checkpoint { project, step, summary, provider?, credits, real_person?, consent? }` **before** every step that costs
  credits, uses a real person's voice or face, or publishes. `step`: character, clip, voice, assemble, copy, publish, other.
  `credits` = your honest estimate in the provider's credits (read the price from the provider's model list; do not guess low).
  - `ok` + `stepId`: run the step once.
  - `waiting_approval`: **do not run it.** Tell the user what is waiting and why. Call the checkpoint again with the SAME arguments
    every 20-30 seconds for a few minutes; it answers `ok` once approved (allowed exactly once) or `rejected` (stop).
  - Never change the arguments (a lower estimate, a vaguer summary) to get around an approval.
- `vellarin_media_log { step_id, status: done|failed, credits, asset_url?, qa?, qa_note?, cta? }` after the step, with what it REALLY
  cost. For free steps with no checkpoint (assembly, captions): `{ project, step, status, ... }`.
- `vellarin_media_status { project? }`: the budget left, what is waiting, the latest steps, and `recentCtas`.

## The flow that works

1. **Script.** 45-58 words for 22-26 seconds. One idea and one call to action per video; read `recentCtas` and use a different one.
   Run `python3 scripts/reel.py plan --script "..."`: it answers the duration to ask for and the lines to add to the prompt.
2. **Character image** (checkpoint, step `character`). 9:16, 2K. Always "a fictional person who does not resemble any real person".
   Describe age range, features, clothes, place, and the sleeves in words: "rolled above the elbow", "at mid forearm" (more natural)
   or "long". A logo on clothes: pass the logo image as a reference so the text comes out right; not every character needs one.
   Look at the image before going on: hands, clothes, legible logo, no stray text.
3. **Cheap test first.** Generate 1-3 clips of different kinds, check them, and only then launch a batch.
4. **Clip** (checkpoint, step `clip`). One continuous take, 1080p, 9:16, the duration from `plan`, the exact script, the prompt
   lines from `plan`. Same voice across clips: pass a reference audio; without it every clip sounds different. Two people: one image
   with both, lines per speaker, "only the person speaking moves their mouth". Generation is asynchronous: poll the provider's task.
5. **Check** every clip: `python3 scripts/reel.py check --video clip.mp4 --script "..." --sheet sheet.png`. Exit code 1 = it lists
   why (ending rushed or cut, words missing, wrong size). Look at the contact sheet yourself. Log the verdict (`qa`, `qa_note`). A
   failed clip is regenerated with a new checkpoint, usually with a shorter duration. A brand name in `missing_words` is usually
   the transcriber mishearing it: listen before regenerating.
6. **Assemble**: `python3 scripts/reel.py assemble --video clip.mp4 --script "..." --out reel.mp4 --y 1440 [--music m.mp3]`.
   Subtitles come from the script, one line, white with outline, no box. `--y` between 1290 and 1535: below a chest logo, clear of
   hands and objects, above the area the apps cover. At most 2-3 renders at once; retry one that was killed.
7. **Captions** (`copy`): title, Instagram text, TikTok text, hashtags. `python3 scripts/reel.py lint --file caption.txt --ban "..."
   --allow-domain example.com` checks banned phrases and links the user gave you.
8. **Publish** only if the user asked, and only after a checkpoint with step `publish` came back `ok`. It always waits for the owner.
   Remind the user to switch on the platform's own label for AI-made content where the platform requires it.

## Rules that do not bend

- **Real people.** Copying a real person's voice or face needs `real_person: true` and `consent` (who agreed, when, where the
  agreement is kept), and always waits for the owner. No consent on record: use a fictional person. Never a lookalike of a third party.
- **Over budget = stop.** A checkpoint that waits is not an error to work around. Do other free work (scripts, captions) meanwhile.
- **Tell the truth in the log.** Report failed steps and their real cost; they were charged too.
- Keep provider keys, tokens and personal data out of `summary` and `note`.

## Setup for reel.py

`ffmpeg` and `ffprobe` on PATH; for check and assemble: `pip install faster-whisper pillow numpy` (a virtual environment is fine).
English speech by default. In a provider sandbox, upload this script there first.
