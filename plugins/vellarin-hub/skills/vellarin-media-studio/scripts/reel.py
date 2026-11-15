#!/usr/bin/env python3
"""Vellarin Media Studio: plan, check and assemble a vertical talking-head reel from ONE generated clip and its script.

Runs on the user's computer or in their generation provider's sandbox. It never calls a provider and needs no key.

  reel.py plan     --script "..."                         duration to ask for, and the lines to add to the generation prompt
  reel.py check    --video clip.mp4 --script "..." [--sheet sheet.png]     QA of a generated clip (exit 1 = regenerate)
  reel.py assemble --video clip.mp4 --script "..." --out reel.mp4 [--y 1440] [--music m.mp3]
  reel.py lint     --file caption.txt [--ban "phrase"]... [--allow-domain example.com]...

Needs: ffmpeg and ffprobe on PATH. check and assemble also need `pip install faster-whisper pillow numpy`.
Subtitles always come from the SCRIPT (the transcription only gives the timing): speech models mishear brand names.
"""
import argparse, difflib, json, math, os, re, shutil, subprocess, sys, tempfile

W, H, FPS = 1080, 1920, 24
WORDS_PER_SEC = 2.3          # measured pace of a brisk single take
TAIL_SEC = 2.0               # silence asked for after the last word
MAX_TAKE_SEC = 26            # past this, models stretch the pace and then rush the ending
MIN_GAP = 0.04               # a subtitle ends at least this long before the next one starts
SAFE_Y = (1290, 1535)        # below the chest logo, above the area the apps cover with their own buttons
FONTS = ["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
         "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", "C:/Windows/Fonts/arialbd.ttf"]

norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
def run(*a): subprocess.run(list(a), check=True)
def out(*a): return subprocess.check_output(list(a)).decode()

# ---------------------------------------------------------------- plan
def plan(script):
    words = len(script.split())
    secs = math.ceil(words / WORDS_PER_SEC + TAIL_SEC)
    warn = []
    if secs > MAX_TAKE_SEC: warn.append(f"{words} words need about {secs} s; keep one take at {MAX_TAKE_SEC} s or less (about {int((MAX_TAKE_SEC - TAIL_SEC) * WORDS_PER_SEC)} words). Shorten the script.")
    if words < 20: warn.append("Under 20 words: the model tends to stretch the pace. Ask for a shorter clip or add a line.")
    return {"words": words, "duration_sec": min(secs, MAX_TAKE_SEC), "warnings": warn,
            "prompt_lines": ["One continuous take, vertical 9:16, 1080p.", "Brisk, natural pace; do not drag the words.",
                             f"Say the script exactly, word for word. Finish the last word with about {int(TAIL_SEC)} seconds of video left.",
                             "A fictional person who does not resemble any real person."]}

# ---------------------------------------------------------------- probe and transcription
def probe(video):
    j = json.loads(out("ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", video))
    v = next((s for s in j["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in j["streams"] if s["codec_type"] == "audio"), None)
    num, den = (v or {}).get("avg_frame_rate", "0/1").split("/")
    return {"width": (v or {}).get("width"), "height": (v or {}).get("height"), "fps": round(float(num) / max(1.0, float(den)), 2), "audio": a is not None, "duration": float(j["format"]["duration"])}

def transcribe(video, tmp):
    """Word timings with faster-whisper small.en + VAD (whisper.cpp with one word per line gave rounded, unusable times)."""
    wav = os.path.join(tmp, "a.wav")
    run("ffmpeg", "-y", "-loglevel", "error", "-i", video, "-vn", "-ar", "16000", "-ac", "1", wav)
    from faster_whisper import WhisperModel
    segs, _ = WhisperModel(os.environ.get("REEL_WHISPER", "small.en"), compute_type="int8").transcribe(wav, word_timestamps=True, language="en", vad_filter=True, condition_on_previous_text=False)
    return [[x.start, x.end, x.word.strip()] for s in segs for x in s.words if x.word.strip()], wav

def align(script, heard):
    """Each script word gets a time: matched words take the heard time, the rest are spread between their neighbours."""
    S = script.split(); sn = [norm(s) for s in S]; wn = [norm(w[2]) for w in heard]
    times = [None] * len(S)
    for a, b, n in difflib.SequenceMatcher(None, sn, wn, autojunk=False).get_matching_blocks():
        for k in range(n): times[a + k] = (heard[b + k][0], heard[b + k][1])
    matched = [t is not None for t in times]
    i = 0
    while i < len(S):
        if times[i] is not None: i += 1; continue
        j = i
        while j < len(S) and times[j] is None: j += 1
        prev = times[i - 1][1] if i > 0 else (heard[0][0] if heard else 0.0)
        nxt = times[j][0] if j < len(S) else (heard[-1][1] if heard else prev + 0.4 * (j - i))
        step = max(0.05, (nxt - prev) / (j - i))
        for q in range(i, j): times[q] = (prev + (q - i) * step, prev + (q - i + 1) * step)
        i = j
    return S, times, matched

# ---------------------------------------------------------------- check (QA)
def sheet(video, duration, path, frames=8):
    run("ffmpeg", "-y", "-loglevel", "error", "-i", video, "-vf", f"fps={frames}/{max(duration, 1):.3f},scale=216:-1,tile={frames}x1", "-frames:v", "1", path)

def check(video, script, sheet_path=None, min_cover=0.92, min_tail=1.0):
    p = probe(video); why = []
    if (p["width"], p["height"]) != (W, H): why.append(f"size is {p['width']}x{p['height']}, expected {W}x{H}")
    if abs(p["fps"] - FPS) > 0.5: why.append(f"frame rate is {p['fps']}, expected {FPS}")
    if not p["audio"]: why.append("no audio track")
    res = {"video": p}
    if p["audio"]:
        with tempfile.TemporaryDirectory() as tmp:
            heard, _ = transcribe(video, tmp)
        S, times, matched = align(script, heard)
        cover = sum(matched) / max(1, len(S)); res["coverage"] = round(cover, 3)
        if cover < min_cover: why.append(f"only {round(cover * 100)}% of the script words were heard (needs {round(min_cover * 100)}%)")
        last3 = matched[-3:]
        if sum(last3) < min(2, len(last3)): why.append("the last words of the script were not heard: the ending is cut or garbled")
        end = heard[-1][1] if heard else 0.0; tail = p["duration"] - end; res["tail_sec"] = round(tail, 2)
        if tail < min_tail: why.append(f"only {tail:.1f} s after the last word (needs {min_tail} s): the ending is at risk of being cut")
        # Rushed ending (a heuristic): characters per second in the last quarter of the words against the rest.
        n = len(S); q = max(3, n // 4)
        rate = lambda lo, hi: sum(len(S[i]) for i in range(lo, hi)) / max(0.2, times[hi - 1][1] - times[lo][0])
        if n >= 12:
            ratio = rate(n - q, n) / max(0.1, rate(0, n - q)); res["ending_pace_ratio"] = round(ratio, 2)
            if ratio > 1.6: why.append(f"the ending is spoken {ratio:.1f}x faster than the rest: ask for a shorter clip (see `plan`) and regenerate")
        res["missing_words"] = [S[i] for i in range(n) if not matched[i]][:20]
    if sheet_path: sheet(video, p["duration"], sheet_path); res["sheet"] = sheet_path
    res["pass"] = not why; res["reasons"] = why
    res["note"] = "A brand name in missing_words is usually the transcriber, not the voice: listen before regenerating."
    return res

# ---------------------------------------------------------------- subtitles
def chunks(S, maxc=30):
    """By clause, balanced, one line each: no orphan fragments such as 'in a / normal day'."""
    clauses, cur = [], []
    for i, w in enumerate(S):
        cur.append(i)
        if re.search(r"[.?!,:;]$", w): clauses.append(cur); cur = []
    if cur: clauses.append(cur)
    text = lambda c: " ".join(S[k] for k in c)
    merged = []
    for c in clauses:
        if merged and len(text(merged[-1])) < 12 and not re.search(r"[.?!]$", S[merged[-1][-1]]) and len(text(merged[-1] + c)) <= maxc: merged[-1] = merged[-1] + c
        else: merged.append(c)
    res = []
    for c in merged:
        L = len(text(c)); n = max(1, math.ceil(L / maxc))
        if n == 1: res.append(c); continue
        target, g, acc, parts = L / n, [], 0, []
        for k in c:
            g.append(k); acc += len(S[k]) + 1
            if acc >= target - 2 and len(parts) < n - 1: parts.append(g); g = []; acc = 0
        if g:
            if parts and len(text(g)) < 8: parts[-1] += g      # never leave a dangling word alone
            else: parts.append(g)
        res += parts
    return res

def phrases(S, times):
    ph = [[times[c[0]][0], times[c[-1]][1], " ".join(S[k] for k in c)] for c in chunks(S)]
    for i in range(len(ph)):
        if ph[i][1] <= ph[i][0]: ph[i][1] = ph[i][0] + 0.4
        if i + 1 < len(ph) and ph[i][1] > ph[i + 1][0] - MIN_GAP: ph[i][1] = max(ph[i][0] + 0.1, ph[i + 1][0] - MIN_GAP)
    return ph

def font_path(arg):
    for f in ([arg] if arg else []) + FONTS:
        if f and os.path.exists(f): return f
    sys.exit("No bold font found. Pass --font /path/to/a-bold.ttf")

def line_png(text, path, font_file, y, size):
    """One line, white with outline and soft shadow, no box."""
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
    font = ImageFont.truetype(font_file, size)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    while d.textlength(text, font=font) > W - 80 and font.size > 30: font = ImageFont.truetype(font_file, font.size - 2)
    x = (W - d.textlength(text, font=font)) / 2
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((x, y + 3), text, font=font, fill=(0, 0, 0, 150), stroke_width=5, stroke_fill=(0, 0, 0, 150))
    img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(5)))
    ImageDraw.Draw(img).text((x, y), text, font=font, fill=(255, 255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0, 255))
    img.save(path)

# ---------------------------------------------------------------- assemble
def assemble(video, script, dest, y=1440, size=50, music=None, music_lufs=-31.0, font=None, keep_tail=0.55):
    if not SAFE_Y[0] <= y <= SAFE_Y[1]: print(f"warning: --y {y} is outside the safe band {SAFE_Y[0]}-{SAFE_Y[1]} (logo above, app buttons below)", file=sys.stderr)
    ff = font_path(font); p = probe(video)
    with tempfile.TemporaryDirectory() as tmp:
        heard, _ = transcribe(video, tmp)
        S, times, matched = align(script, heard)
        ph = phrases(S, times)
        end = min(p["duration"], ph[-1][1] + keep_tail)
        inputs, chain, prev = ["-i", video], [], "base"
        chain.append(f"[0:v]scale={W}:{H}:flags=lanczos,fps={FPS},format=yuv420p[base]")
        for i, (a, b, text) in enumerate(ph):
            f = os.path.join(tmp, f"s{i}.png"); line_png(text, f, ff, y, size)
            inputs += ["-i", f]
            chain.append(f"[{prev}][{i + 1}:v]overlay=0:0:enable='between(t,{a:.2f},{b:.2f})'[v{i}]"); prev = f"v{i}"
        voice = os.path.join(tmp, "voice.mp4")
        run("ffmpeg", "-y", "-loglevel", "error", *inputs, "-t", f"{end:.3f}", "-filter_complex", ";".join(chain), "-map", f"[{prev}]", "-map", "0:a",
            "-af", f"loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000,afade=t=out:st={max(0, end - 0.08):.3f}:d=0.08",
            "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-movflags", "+faststart", voice)
        if music:
            fo = max(0.0, end - 2.0)
            run("ffmpeg", "-y", "-loglevel", "error", "-i", voice, "-i", music, "-filter_complex",
                f"[1:a]atrim=0:{end:.3f},loudnorm=I={music_lufs}:TP=-3:LRA=7,afade=t=in:d=1.2,afade=t=out:st={fo:.2f}:d=2.0[m];[0:a][m]amix=inputs=2:normalize=0:duration=first,loudnorm=I=-15:TP=-1.5:LRA=11[a]",
                "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", dest)
        else: shutil.copy(voice, dest)
    overlaps = [i for i in range(len(ph) - 1) if ph[i][1] > ph[i + 1][0] - MIN_GAP + 1e-6]
    return {"out": dest, "duration_sec": round(end, 2), "subtitles": [[round(a, 2), round(b, 2), t] for a, b, t in ph], "overlaps": overlaps,
            "matched": round(sum(matched) / max(1, len(S)), 2), "y": y}

# ---------------------------------------------------------------- lint of captions
def lint(text, ban, allow_domains):
    why = []
    for b in ban:
        if re.search(re.escape(b).replace(r"\-", "[- ]?").replace(r"\ ", "[- ]?"), text, re.I): why.append(f'contains the banned phrase "{b}"')
    for u in re.findall(r"(?:https?://)?((?:[a-z0-9-]+\.)+[a-z]{2,})(?:/\S*)?", text, re.I):
        if allow_domains and not any(u.lower() == d or u.lower().endswith("." + d) for d in allow_domains): why.append(f"link to {u} is not on the allowed list")
    return {"pass": not why, "reasons": why}

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); sub = ap.add_subparsers(dest="cmd", required=True)
    def script_args(p): p.add_argument("--script"); p.add_argument("--script-file")
    p = sub.add_parser("plan"); script_args(p)
    p = sub.add_parser("check"); script_args(p); p.add_argument("--video", required=True); p.add_argument("--sheet")
    p = sub.add_parser("assemble"); script_args(p); p.add_argument("--video", required=True); p.add_argument("--out", required=True); p.add_argument("--y", type=int, default=1440)
    p.add_argument("--size", type=int, default=50); p.add_argument("--music"); p.add_argument("--music-lufs", type=float, default=-31.0); p.add_argument("--font")
    p = sub.add_parser("lint"); p.add_argument("--text"); p.add_argument("--file"); p.add_argument("--ban", action="append", default=[]); p.add_argument("--allow-domain", action="append", default=[])
    a = ap.parse_args()
    if a.cmd == "lint":
        r = lint(a.text if a.text is not None else open(a.file, encoding="utf-8").read(), a.ban, [d.lower() for d in a.allow_domain])
    else:
        script = a.script if a.script else open(a.script_file, encoding="utf-8").read() if a.script_file else sys.exit("--script or --script-file is required")
        script = " ".join(script.split())
        r = plan(script) if a.cmd == "plan" else check(a.video, script, a.sheet) if a.cmd == "check" else assemble(a.video, script, a.out, a.y, a.size, a.music, a.music_lufs, a.font)
    print(json.dumps(r, ensure_ascii=False, indent=1))
    sys.exit(0 if r.get("pass", True) else 1)

if __name__ == "__main__": main()
