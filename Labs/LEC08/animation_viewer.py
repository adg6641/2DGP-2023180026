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


def display_scale(frame):
    # 모든 포즈의 실제 캐릭터 높이를 화면 절반 이상으로 표시한다.
    desired_height = WINDOW_HEIGHT * 0.53
    scale = max(1.0, desired_height / frame.height)
    if frame.width * scale > WINDOW_WIDTH - 96:
        scale = (WINDOW_WIDTH - 96) / frame.width
    return scale


class Playback:
    def __init__(self, animations):
        if not animations:
            raise ValueError('Playback needs at least one animation')
        self.animations = animations
        self.animation_index = 0
        self.elapsed = 0.0

    @property
    def animation(self):
        return self.animations[self.animation_index]

    @property
    def frame_index(self):
        if self.resting:
            return len(self.animation.frames) - 1
        return int(self.elapsed / self.animation.frame_seconds) % len(self.animation.frames)

    @property
    def resting(self):
        return self.elapsed >= play_seconds(self.animation)

    @property
    def rest_remaining(self):
        return max(0.0, play_seconds(self.animation) + REST_SECONDS - self.elapsed)

    @property
    def completed_repeats(self):
        return min(REPEAT_COUNT, int(self.elapsed / self.animation.cycle_seconds))

    def update(self, seconds):
        if not math.isfinite(seconds) or seconds < 0:
            raise ValueError('Elapsed time must be finite and nonnegative')
        self.elapsed += seconds
        # 큰 시간 간격에서도 나머지 시간을 버리지 않고 다음 동작으로 전달한다.
        while self.elapsed >= play_seconds(self.animation) + REST_SECONDS:
            self.elapsed -= play_seconds(self.animation) + REST_SECONDS
            self.animation_index = (self.animation_index + 1) % len(self.animations)


def play_seconds(animation):
    return animation.cycle_seconds * REPEAT_COUNT


def run_viewer():
    import pico2d as p
    data, animations = load_manifest()
    validate_manifest(data, animations)
    p.open_canvas(WINDOW_WIDTH, WINDOW_HEIGHT)
    try:
        sheet = load_sheet(p, data)
        player = Playback(animations)
        running = True
        previous = time.perf_counter()
        while running:
            now = time.perf_counter()
            player.update(now - previous)
            previous = now
            for event in p.get_events():
                if event.type == p.SDL_QUIT or (event.type == p.SDL_KEYDOWN and event.key == p.SDLK_ESCAPE):
                    running = False
            if not running:
                break
            p.clear_canvas()
            frame = player.animation.frames[player.frame_index]
            draw_frame(sheet, frame, WINDOW_WIDTH / 2, FLOOR_Y, display_scale(frame))
            p.update_canvas()
            p.delay(0.005)
    finally:
        p.close_canvas()


def main():
    run_viewer()


if __name__ == '__main__':
    main()
