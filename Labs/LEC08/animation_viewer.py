"""Drill #8: a metadata-driven pico2d sprite animation viewer."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

from dataclasses import dataclass
import json
import math
import time

WINDOW_WIDTH = 960
WINDOW_HEIGHT = 640
REPEAT_COUNT = 5
REST_SECONDS = 1.0
FLOOR_Y = 88


@dataclass(frozen=True)
class Frame:
    x: int
    y: int
    width: int
    height: int
    pivot_x: float
    pivot_y: float


@dataclass(frozen=True)
class Animation:
    name: str
    label: str
    frame_seconds: float
    frames: tuple[Frame, ...]

    @property
    def cycle_seconds(self):
        return len(self.frames) * self.frame_seconds


def main():
    import pico2d as p
    p.open_canvas(960, 640)
    try:
        p.clear_canvas()
        p.update_canvas()
        p.delay(0.2)
    finally:
        p.close_canvas()


if __name__ == '__main__':
    main()
