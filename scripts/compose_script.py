#!/usr/bin/env python3
import json
import os
import sys
import time
from pathlib import Path

import requests

OPENROUTER_KEY = os.environ["OPENROUTER_API_KEY"]
MODEL = "moonshotai/kimi-k2.5"

SYSTEM_PROMPT = """You are a crypto-noir narrator writing 30-second video scripts.
Scripts are cinematic, factual, no emoji, no hashtags.
Each act has narrator text plus a value to animate.
Output ONLY a single JSON object. No prose, no markdown, no code fences."""

USER_TEMPLATE = """Event data:
{event_json}

Write a 30-second video script as JSON with EXACTLY this schema:
{{
  "title": "string, max 50 chars, no quotes",
  "act1_setup": {{
    "text": "narrator line, 8-15 words, sets the scene",
    "value_label": "what number to animate",
    "value_from": 0,
    "value_to": <number>
  }},
  "act2_action": {{
    "text": "narrator line, 15-25 words, the action unfolding",
    "value_label": "what number to animate",
    "value_from": <number>,
    "value_to": <number>
  }},
  "act3_aftermath": {{
    "text": "narrator line, 10-18 words, the consequence",
    "value_label": "what number to animate",
    "value_from": <number>,
    "value_to": <number>
  }},
  "tagline": "string, max 60 chars, the takeaway"
}}

Rules:
- Total narrator text under 350 characters.
- Use real numbers from the event.
- No special chars in text: no $, no backslashes, no quotes.
- Tone: detached observer, documentary."""


def call_kimi(event_json: dict) -> dict:
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/lore-engine",
            "X-Title": "Lore Engine",
        },
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_TEMPLATE.format(
                    event_json=json.dumps(event_json, indent=2)
                )},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.7,
            "max_tokens": 1500,
            "reasoning": {"enabled": False},
            "provider": {"require_parameters": True},
        },
        timeout=90,
    )
    response.raise_for_status()
    data = response.json()
    msg = data["choices"][0]["message"]
    raw = msg.get("content")
    if not raw:
        raw = msg.get("reasoning") or ""
        if isinstance(msg.get("reasoning_details"), list):
            for d in msg["reasoning_details"]:
                if d.get("text"):
                    raw = d["text"]
                    break
    if not raw:
        raise RuntimeError(f"no content and no reasoning in response: {data}")

    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    return json.loads(raw)


def validate(script: dict) -> None:
    required_acts = ["act1_setup", "act2_action", "act3_aftermath"]
    for k in ["title", "tagline"] + required_acts:
        assert k in script, f"missing key: {k}"
    for act in required_acts:
        a = script[act]
        for f in ["text", "value_label", "value_from", "value_to"]:
            assert f in a, f"{act} missing {f}"
        assert "$" not in a["text"], f"{act}: dollar sign breaks Manim"
        assert "\\" not in a["text"], f"{act}: backslash breaks Manim"
    total_chars = sum(len(script[a]["text"]) for a in required_acts)
    assert total_chars < 400, f"text too long: {total_chars}"


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: compose_script.py <event_json_path>", file=sys.stderr)
        sys.exit(2)

    event_path = Path(sys.argv[1])
    event = json.loads(event_path.read_text())
    out_path = event_path.parent / "script.json"

    last_err = None
    for attempt in range(2):
        try:
            script = call_kimi(event)
            validate(script)
            out_path.write_text(json.dumps(script, indent=2, ensure_ascii=False))
            print(f"OK: script written to {out_path}")
            print(json.dumps(script, indent=2, ensure_ascii=False))
            return
        except Exception as e:
            last_err = e
            print(f"attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(2)
    raise SystemExit(f"failed after 2 attempts: {last_err}")


if __name__ == "__main__":
    main()
