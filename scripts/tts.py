#!/usr/bin/env python3
"""tts.py - ElevenLabs voice-over for the lore script."""
import json
import os
import sys
from pathlib import Path

import requests

ELEVEN_KEY = os.environ["ELEVENLABS_API_KEY"]
# "Adam" — pre-made voice, low male, dramatic. Free tier voice.
VOICE_ID = "CwhRBWXzGAHq8TQ4Fs17"


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: tts.py <script.json>", file=sys.stderr)
        sys.exit(2)

    script = json.loads(Path(sys.argv[1]).read_text())
    full_text = " ... ".join([
        script["act1_setup"]["text"],
        script["act2_action"]["text"],
        script["act3_aftermath"]["text"],
        script["tagline"],
    ])

    if len(full_text) > 500:
        print(f"WARN: text length {len(full_text)} eats free tier fast", file=sys.stderr)

    r = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}",
        headers={
            "xi-api-key": ELEVEN_KEY,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
        json={
            "text": full_text,
            "model_id": "eleven_turbo_v2_5",  # fastest, free-tier friendly
            "voice_settings": {
                "stability": 0.55,
                "similarity_boost": 0.75,
                "style": 0.4,
            },
        },
        timeout=60,
    )
    r.raise_for_status()

    out = Path("voiceover.mp3")
    out.write_bytes(r.content)
    print(f"OK: voiceover written to {out} ({len(r.content)} bytes)")


if __name__ == "__main__":
    main()
