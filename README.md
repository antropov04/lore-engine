# Lore Engine — On-chain → Cinematic Clip

A Hermes Agent skill that turns any Ethereum transaction into a 30-second
narrated video clip. Uses Kimi K2.5 (free on OpenRouter) for the script,
Manim for visuals, ElevenLabs for voice-over, ffmpeg to glue it together.

Built for the Nous Research Hermes Agent Creative Hackathon.

## What it does

You give Hermes a tx hash. Hermes hands it to Kimi K2.5. Kimi reads the
on-chain data, picks an angle, writes a 3-act narrator script, returns
strict JSON. The skill renders a fixed Manim scene with that script,
generates voice-over, mixes background music, outputs `final.mp4`.

Total cost per clip: ~$0.005 (free Kimi + ElevenLabs free tier).

## Install

```bash
hermes skills install github.com/<your-handle>/lore-engine
```

Or manually clone into `~/.hermes/skills/creative/lore-engine/`.

## Use

```
> /lore-engine 0xabc123...
```

Or just paste a tx hash in chat — the skill auto-triggers.

## Required env vars

```bash
export ETHERSCAN_API_KEY=...      # free at etherscan.io/apis
export OPENROUTER_API_KEY=...     # for free Kimi K2.5
export ELEVENLABS_API_KEY=...     # free tier 10k chars/month
```

## Dependencies

- `manim` (Community Edition) + ffmpeg + LaTeX
  - macOS: `brew install manim`
  - Ubuntu: `apt install ffmpeg texlive` then `pip install manim`
- Python 3.10+
- `requests`

## Why Kimi K2.5

K2.5 is multimodal, free on OpenRouter, and follows JSON schemas
reliably. On-chain data fits its long context cleanly. The script
falls back to Kimi K2 Thinking if the free tier rate-limits.

MIT.
