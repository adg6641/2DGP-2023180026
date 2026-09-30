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


def load_manifest(path=BASE_DIR / 'assets' / 'sprite_atlas.json'):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    animations = tuple(
        Animation(item['name'], item['label'], item['frame_seconds'],
                  tuple(Frame(**frame) for frame in item['frames']))
        for item in data['animations']
    )
    return data, animations


def validate_manifest(data, animations):
    if data.get('schema_version') != 1:
        raise ValueError('Unsupported sprite manifest schema')
    width, height = data['size']
    if not isinstance(width, int) or not isinstance(height, int) or min(width, height) <= 0:
        raise ValueError('Atlas dimensions must be positive integers')
    if len(animations) < 4:
        raise ValueError('At least four animations are required')
    if len({a.name for a in animations}) != len(animations):
        raise ValueError('Animation names must be unique')
    for animation in animations:
        if not animation.frames or not math.isfinite(animation.frame_seconds) or animation.frame_seconds <= 0:
            raise ValueError('Each animation needs frames and a positive frame duration')
        for frame in animation.frames:
            if any(not isinstance(v, int) for v in (frame.x, frame.y, frame.width, frame.height)):
                raise ValueError('Frame bounds must use integer pixels')
            if min(frame.x, frame.y) < 0 or min(frame.width, frame.height) <= 0:
                raise ValueError('Invalid frame rectangle')
            if frame.x + frame.width > width or frame.y + frame.height > height:
                raise ValueError('Frame rectangle exceeds the atlas')
            if not (0 <= frame.pivot_x <= frame.width and 0 <= frame.pivot_y <= frame.height):
                raise ValueError('Frame pivot must lie inside its rectangle')


def load_sheet(p, data):
    path = BASE_DIR / 'assets' / data['image']
    if path.parent.resolve() != (BASE_DIR / 'assets').resolve():
        raise ValueError('Atlas image must be inside assets')
    if not path.is_file():
        raise FileNotFoundError(f'Sprite atlas not found: {path}')
    sheet = p.load_image(str(path))
    if [sheet.w, sheet.h] != data['size']:
        raise ValueError('Atlas image dimensions do not match the manifest')
    return sheet


def clip_rectangle(frame, atlas_height):
    # JSON/Pillow 좌표는 왼쪽 위, pico2d의 clip 좌표는 왼쪽 아래이다.
    return (frame.x, atlas_height - frame.y - frame.height,
            frame.width, frame.height)


def draw_frame(sheet, frame, x, y, scale=1.0):
    # pivot은 크롭된 프레임 내부의 발밑 중심이다. 크기가 바뀌어도 중심이 유지된다.
    center_x = x + (frame.width / 2 - frame.pivot_x) * scale
    center_y = y + (frame.pivot_y - frame.height / 2) * scale
    sheet.clip_draw(*clip_rectangle(frame, sheet.h), center_x, center_y,
                    round(frame.width * scale), round(frame.height * scale))


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
