"""manim_template.py - Fixed Manim scene for Lore Engine clips (no LaTeX)."""
import json
from pathlib import Path

from manim import (
    Scene, Text, Write, FadeIn, FadeOut, ValueTracker,
    always_redraw,
    UP, DOWN, LEFT, RIGHT, ORIGIN, WHITE, GREEN, RED, YELLOW,
    config,
)

config.pixel_height = 1920
config.pixel_width = 1080
config.frame_height = 16.0
config.frame_width = 9.0
config.background_color = "#0a0a0a"

SCRIPT = json.loads(Path("script.json").read_text())


def _fmt(v: float) -> str:
    """Format a number for display: no decimals for big values, with commas."""
    if abs(v) >= 1000:
        return f"{int(round(v)):,}"
    if abs(v) >= 1:
        return f"{v:.2f}"
    return f"{v:.4f}"


class LoreClip(Scene):
    def construct(self) -> None:
        # ---- TITLE CARD (0-2s) ----
        title = Text(
            SCRIPT["title"],
            color=WHITE,
            weight="BOLD",
            font_size=56,
        ).to_edge(UP, buff=1.5)
        self.play(Write(title, run_time=1.2))
        self.wait(0.5)

        self._play_act(SCRIPT["act1_setup"], color=YELLOW, run_time=7)
        self._play_act(SCRIPT["act2_action"], color=GREEN, run_time=11)
        self._play_act(SCRIPT["act3_aftermath"], color=RED, run_time=5)

        # ---- TAGLINE (final) ----
        self.clear()
        tagline = Text(
            SCRIPT["tagline"],
            color=WHITE,
            font_size=44,
        ).move_to(ORIGIN)
        if tagline.width > 8.0:
            tagline.scale(8.0 / tagline.width)
        watermark = Text(
            "made by hermes agent on kimi k2.5",
            color="#666666",
            font_size=24,
        ).to_edge(DOWN, buff=1.0)
        self.play(FadeIn(tagline), FadeIn(watermark), run_time=1.0)
        self.wait(1.0)

    def _play_act(self, act: dict, color, run_time: float) -> None:
        self.clear()

        narrator = Text(
            act["text"],
            color=WHITE,
            font_size=36,
            line_spacing=1.2,
        ).to_edge(UP, buff=1.0)
        if narrator.width > 8.0:
            narrator.scale(8.0 / narrator.width)

        v_from = float(act["value_from"])
        v_to = float(act["value_to"])
        tracker = ValueTracker(v_from)

        # Use Text (no LaTeX) instead of DecimalNumber
        counter = always_redraw(lambda: Text(
            _fmt(tracker.get_value()),
            color=color,
            font_size=120,
            weight="BOLD",
        ).move_to(ORIGIN))

        label = Text(
            act["value_label"],
            color="#999999",
            font_size=32,
        )
        # position label just below where counter will be
        label.move_to(ORIGIN).shift(DOWN * 2)

        self.add(narrator, counter, label)
        self.play(FadeIn(narrator), run_time=0.6)
        self.play(
            tracker.animate.set_value(v_to),
            run_time=run_time - 1.2,
        )
        self.wait(0.5)
