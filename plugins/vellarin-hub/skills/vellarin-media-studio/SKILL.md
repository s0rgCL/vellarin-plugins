---
name: vellarin-media-studio
description: Make images and short vertical videos (Instagram Reels, TikTok) of a realistic fictional person speaking a script, with subtitles, through Vellarin Hub with one key. Hub sends each request to the generation provider the workspace owner connected (their own account), under the owner's spending limits and approvals, and keeps the record. Use when the user asks for an image, a reel, a talking-head video, a batch of brand videos, or captions for them, and the Vellarin MCP server (tools vellarin_media_generate_video, vellarin_media_task, vellarin_media_status) is available.
---

# Vellarin Media Studio

You generate **through Vellarin Hub**: the `vellarin_media_generate_*` tools send each request to the generation provider the workspace
owner connected with **their own account** (their credits; today Buzzy). Hub is in the middle on purpose: every request goes through
the owner's limits before it reaches the provider, and every step is recorded. `scripts/reel.py` (in this skill) plans, checks and
assembles; it runs on the user's computer and needs no key.

- `provider_not_connected`: nothing can be generated yet. Tell the user: the workspace owner connects their generation account once
  at https://agents.vellarin.ai/agents/developers (Media Studio). Do not look for another way to generate.
- `provider_reconnect`: the owner connects it again in the same place.

## The tools

- `vellarin_media_models {}`: the provider's models with the resolutions, aspect ratios and durations each takes, and `rates`,
  the owner's price list in provider credits. Call it first and copy values verbatim; invented values fail.
- `vellarin_media_generate_image { project, prompt, model, resolution, aspect_ratio, image_urls?, summary? }`
- `vellarin_media_generate_video { project, prompt, model, duration, resolution, aspect_ratio, image_urls?, audio_urls?, summary? }`
- `vellarin_media_generate_audio { project, prompt, model, mode, duration?, provider?, voice_id?, summary? }`
  Every generate tool answers one of:
  - `submitted` + `stepId`: it was sent. Follow it with `vellarin_media_task`.
  - `waiting_approval`: **nothing was sent.** Tell the user what is waiting and why (the answer says why). Call the SAME tool with
    the SAME arguments every 20-30 seconds for a few minutes; it is sent once the owner approves, or answers `rejected` (stop).
  - Never change the arguments (a shorter summary, another estimate) to get around an approval, and never send a request twice
    because it is slow: the same request while its task runs answers that task.
- `vellarin_media_task { step_id }`: `running`, `done` with `urls`, or `failed` with the reason. Ask every 20-30 seconds.
  Images take seconds; video takes several minutes.
- `vellarin_media_log { step_id, status, qa?, qa_note?, cta? }`: record your verdict on a result, or a free step with
  `{ project, step, status }` (assembly, captions).
- `vellarin_media_status { project? }`: the budget left, what is waiting, the latest steps, and `recentCtas`.
- `vellarin_media_checkpoint { project, step: "publish", summary }`: before publishing anywhere. It always waits for the owner.
- **Cost.** The provider reports no price. When `rates` has a price for the kind of step, Hub uses it. When it does not, pass
  `credits` with your honest estimate from the provider's price page, or the request waits for approval as "cost not known".

## The flow that works

1. **Script.** 45-58 words for 22-26 seconds. One idea and one call to action per video; read `recentCtas` and use a different one.
   Run `python3 scripts/reel.py plan --script "..."`: it answers the duration to ask for and the lines to add to the prompt.
2. **Character image** (`vellarin_media_generate_image`). 9:16, 2K. Always "a fictional person who does not resemble any real
   person". Describe age range, features, clothes, place, and the sleeves in words: "rolled above the elbow", "at mid forearm" (more
   natural) or "long". A logo on clothes: pass the logo image in `image_urls` so the text comes out right; not every character
   needs one. Look at the image before going on: hands, clothes, legible logo, no stray text.
3. **Cheap test first.** Generate 1-3 clips of different kinds, check them, and only then launch a batch.
4. **Clip** (`vellarin_media_generate_video`). One continuous take, 1080p, 9:16, the duration from `plan`, the exact script and the
   prompt lines from `plan` in `prompt`, the character image in `image_urls`. Same voice across clips: pass a reference audio in
   `audio_urls`; without it every clip sounds different. Two people: one image with both, lines per speaker, "only the person
   speaking moves their mouth".
5. **Check** every clip: download it, then `python3 scripts/reel.py check --video clip.mp4 --script "..." --sheet sheet.png`. Exit
   code 1 = it lists why (ending rushed or cut, words missing, wrong size). Look at the contact sheet yourself. Log the verdict
   (`qa`, `qa_note`). A failed clip is generated again as a new request, usually with a shorter duration. A brand name in
   `missing_words` is usually the transcriber mishearing it: listen before generating again.
6. **Assemble**: `python3 scripts/reel.py assemble --video clip.mp4 --script "..." --out reel.mp4 --y 1440 [--music m.mp3]`.
   Subtitles come from the script, one line, white with outline, no box. `--y` between 1290 and 1535: below a chest logo, clear of
   hands and objects, above the area the apps cover. At most 2-3 renders at once; retry one that was killed.
7. **Captions**: title, Instagram text, TikTok text, hashtags. `python3 scripts/reel.py lint --file caption.txt --ban "..."
   --allow-domain example.com` checks banned phrases and links the user gave you.
8. **Publish** only if the user asked, and only after `vellarin_media_checkpoint` with step `publish` came back `ok`. Remind the
   user to switch on the platform's own label for AI-made content where the platform requires it.

## Rules that do not bend

- **Real people.** Copying a real person's voice or face needs `real_person: true` and `consent` (who agreed, when, where the
  agreement is kept), and always waits for the owner. No consent on record: use a fictional person. Never a lookalike of a third party.
- **Over budget = stop.** A request that waits is not an error to work around. Do free work (scripts, captions) meanwhile.
- **One way in.** With a Hub key, generate only through these tools. Do not use another generation connector for the same work:
  it would skip the owner's limits and the record.
- Keep keys, tokens and personal data out of `summary` and notes.

## Setup for reel.py

`ffmpeg` and `ffprobe` on PATH; for check and assemble: `pip install faster-whisper pillow numpy` (a virtual environment is fine).
English speech by default.
