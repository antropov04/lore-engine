---
name: lore-engine
description: |
  Turn any Ethereum on-chain event into a 30-second cinematic video clip.
  Fetches the transaction, asks Kimi K2.5 to write a 3-act narrative,
  renders it as a Manim animation with synchronized voice-over and
  background music. Final output is a publish-ready MP4.
  Trigger when the user pastes a transaction hash, an Ethereum address,
  or asks for "a video about this transaction" / "make me a clip about
  this whale move" / "lore for this exploit".
version: 1.0.0
metadata:
  hermes:
    tags: [crypto, web3, video, kimi, manim, creative]
    category: creative
required_environment_variables:
  - name: ETHERSCAN_API_KEY
    prompt: Etherscan API key (free at etherscan.io/apis)
    required_for: full functionality
  - name: ELEVENLABS_API_KEY
    prompt: ElevenLabs API key (free tier, 10k chars/month)
    required_for: voice-over generation
  - name: OPENROUTER_API_KEY
    prompt: OpenRouter API key for Kimi K2.5 (free model)
    required_for: script writing

required_python_packages:
  - requests (for Etherscan API calls)
  - manim (for video rendering, typically in a venv)
---

# Lore Engine

## When to Use
Trigger this skill when the input is one of:
- A transaction hash (0x followed by 64 hex chars)
- An Ethereum address (0x followed by 40 hex chars)
- A natural-language ask: "make a video about this tx", "lore this whale",
  "clip this exploit", "tell me the story of this NFT mint"

## Procedure

### Step 1 — Fetch event data
Run `scripts/fetch_event.py <hash_or_address>`. Returns JSON with:
- value_eth, value_usd, gas_eth
- from_addr, to_addr, from_ens, to_ens
- token_transfers (list of {token, amount, symbol})
- event_type (one of: transfer, swap, mint, exploit_candidate, contract_creation)
- timestamp_iso

### Step 2 — Compose narrative (Kimi K2.5)
Run `scripts/compose_script.py <event_json_path>`. The script calls Kimi K2.5
with a strict JSON-output prompt that produces three acts:

```json
{
  "title": "max 50 chars",
  "act1_setup": {"text": "narrator line, 2-3 seconds", "value_to_animate": "0.0 -> 4_200_000"},
  "act2_action": {"text": "narrator line, 8-12 seconds", "value_to_animate": "X -> Y"},
  "act3_aftermath": {"text": "narrator line, 5-7 seconds", "value_to_animate": "Y -> Z"},
  "tagline": "max 60 chars, appears as final card"
}
```

CRITICAL: Kimi must output ONLY valid JSON. Use response_format json_object
in the API call. If parse fails, retry once with stricter prompt.

### Step 3 — Render video (Manim)
Run `scripts/render_video.py <script_json>`. Uses templates/manim_template.py
which is a pre-validated Manim Scene that takes JSON and renders 30s.
Output: ~/.hermes/lore-engine-output/{date}/{hash}/scene.mp4

DO NOT let Kimi write Manim code from scratch. Template is fixed; Kimi only
provides text + numbers via JSON.

### Step 4 — Generate voice-over (ElevenLabs)
Run `scripts/tts.py <script_json>`. Concatenates act1+act2+act3 text,
sends to ElevenLabs voice "Adam" (low male, dramatic). Returns voiceover.mp3.
Watch the 10k char/month budget — typical clip uses ~400 chars.

### Step 5 — Mux final video
Run `scripts/mux.py`. Uses ffmpeg to combine:
- scene.mp4 (visuals)
- voiceover.mp3 (narrator)
- assets/bg_loop.mp3 at -18dB (background)
Output: final.mp4 (30s, 1080x1920 vertical for X/Telegram autoplay)

### Step 6 — Preview and publish
Show final.mp4 path to user. If user confirms "ship it":
- Save to ~/.hermes/lore-engine-output/{date}/{hash}/
- Create memory entry: "Generated lore video for tx {hash}, type: {event_type}"

## Pitfalls
- Kimi sometimes wraps JSON in ```json fences — strip them in compose_script.py
- Manim LaTeX errors if narrator text contains $ or backslashes — sanitize first
- ffmpeg fails silently if voiceover.mp3 longer than 30s — pad/truncate scene.mp4
- ElevenLabs throttles free tier on parallel calls — never run more than 1 at a time
- Etherscan returns "Max rate limit reached" if no API key — always require key
- Manim render takes 25-40s per clip on M-series Mac, 60-90s on x86 Linux

## Verification
A successful run produces:
- final.mp4 file, 30 seconds ±2s, 1080x1920, with audio
- One JSON archive of the Kimi script
- Memory entry recording event type and final mp4 path
