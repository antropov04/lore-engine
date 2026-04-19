#!/usr/bin/env python3
"""render_and_mux.py - Manim render + ffmpeg mux, no preview, explicit paths."""
import shutil
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_DIR / "templates" / "manim_template.py"
BG_MUSIC = SKILL_DIR / "assets" / "bg_loop.mp3"


def run(cmd: list[str]) -> None:
    print(f"$ {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def main() -> None:
    cwd = Path.cwd()
    local_template = cwd / "manim_template.py"
    shutil.copy(TEMPLATE, local_template)

    quality = sys.argv[1] if len(sys.argv) > 1 else "l"
    # No -p (no preview), --disable_caching to force fresh render
    run([
        "manim",
        f"-q{quality}",
        "--disable_caching",
        "--resolution", "1080,1920",
        "--fps", "30",
        "manim_template.py",
        "LoreClip",
    ])

    candidates = list((cwd / "media" / "videos" / "manim_template").glob("*/LoreClip.mp4"))
    if not candidates:
        print("ERROR: Manim output not found", file=sys.stderr)
        sys.exit(1)
    # Pick the newest file (by mtime) in case multiple quality levels exist
    scene_mp4 = max(candidates, key=lambda p: p.stat().st_mtime)
    print(f"Manim output: {scene_mp4} ({scene_mp4.stat().st_size // 1024} KB)")

    voice = cwd / "voiceover.mp3"
    if not voice.exists():
        print(f"ERROR: {voice} missing", file=sys.stderr)
        sys.exit(1)

    if not BG_MUSIC.exists():
        print(f"No bg music at {BG_MUSIC}, muxing voiceover only")
        run([
            "ffmpeg", "-y",
            "-i", str(scene_mp4),
            "-i", str(voice),
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "final.mp4",
        ])
    else:
        run([
            "ffmpeg", "-y",
            "-i", str(scene_mp4),
            "-i", str(voice),
            "-stream_loop", "-1", "-i", str(BG_MUSIC),
            "-filter_complex",
            "[1:a]volume=1.0[voice];"
            "[2:a]volume=0.18[bg];"
            "[voice][bg]amix=inputs=2:duration=first:dropout_transition=0[aout]",
            "-map", "0:v:0",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "final.mp4",
        ])

    # Sanity check — confirm audio is in the output
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0",
         "-show_entries", "stream=codec_name", "-of", "default=noprint_wrappers=1:nokey=1",
         "final.mp4"],
        capture_output=True, text=True,
    )
    audio_codec = result.stdout.strip()
    size_kb = Path("final.mp4").stat().st_size // 1024
    if audio_codec:
        print(f"OK: final.mp4 written ({size_kb} KB, audio: {audio_codec})")
    else:
        print(f"WARN: final.mp4 has NO audio stream ({size_kb} KB)")
        sys.exit(1)


if __name__ == "__main__":
    main()
