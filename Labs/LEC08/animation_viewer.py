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


def load_ui_fonts(p):
    import os
    candidates = [
        Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts' / 'consola.ttf',
        Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),
        Path('/System/Library/Fonts/Monaco.ttf'),
    ]
    for path in candidates:
        if path.is_file():
            return p.load_font(str(path), 27), p.load_font(str(path), 16)
    raise FileNotFoundError('A UI font is required (Consolas or DejaVu Sans)')


def draw_backdrop(p):
    p.draw_rectangle(0, 0, WINDOW_WIDTH - 1, WINDOW_HEIGHT - 1, 15, 20, 32, filled=True)
    p.draw_rectangle(24, 63, WINDOW_WIDTH - 25, WINDOW_HEIGHT - 116, 23, 31, 47, filled=True)
    p.draw_rectangle(24, FLOOR_Y - 8, WINDOW_WIDTH - 25, FLOOR_Y - 7, 66, 90, 110, filled=True)


def draw_hud(p, fonts, player, suspended):
    title, small = fonts
    mint, muted = (110, 235, 207), (160, 177, 198)
    title.draw(28, WINDOW_HEIGHT - 35, 'SPRITE / MOTION LAB', mint)
    small.draw(28, WINDOW_HEIGHT - 67, 'DRILL 08  |  AI PIXEL ART  |  IRREGULAR ATLAS', muted)
    action = player.animation
    status = 'PAUSED' if suspended else ('REST 1s' if player.resting else 'PLAYING')
    repeat = REPEAT_COUNT if player.resting else player.completed_repeats + 1
    small.draw(28, WINDOW_HEIGHT - 96,
               f'{action.label.upper()}   {status}   CYCLE {repeat}/{REPEAT_COUNT}   FRAME {player.frame_index + 1}/{len(action.frames)}', mint)
    small.draw(28, 29, 'SPACE pause/resume    R restart    B frame bounds    ESC exit', muted)


def draw_sequence(p, fonts, player):
    for index, action in enumerate(player.animations):
        x = 585 + index * 91
        color = (110, 235, 207) if index == player.animation_index else (83, 103, 128)
        p.draw_rectangle(x, WINDOW_HEIGHT - 73, x + 77, WINDOW_HEIGHT - 70, *color, filled=True)
        fonts[1].draw(x, WINDOW_HEIGHT - 50, action.label.upper(), color)
    duration = play_seconds(player.animation)
    progress = min(1.0, player.elapsed / duration)
    p.draw_rectangle(28, 53, WINDOW_WIDTH - 29, 55, 46, 60, 81, filled=True)
    if progress > 0:
        p.draw_rectangle(28, 53, 28 + round((WINDOW_WIDTH - 57) * progress), 55,
                         110, 235, 207, filled=True)
    if player.resting:
        fonts[1].draw(WINDOW_WIDTH - 240, WINDOW_HEIGHT - 96,
                      f'NEXT IN {player.rest_remaining:.2f}s', (245, 199, 111))


def draw_bounds(p, fonts, sheet, frame, scale):
    left = WINDOW_WIDTH / 2 - frame.pivot_x * scale
    bottom = FLOOR_Y - (frame.height - frame.pivot_y) * scale
    p.draw_rectangle(left, bottom, left + frame.width * scale,
                     bottom + frame.height * scale, 245, 199, 111)
    p.draw_rectangle(WINDOW_WIDTH / 2 - 3, FLOOR_Y - 3,
                     WINDOW_WIDTH / 2 + 3, FLOOR_Y + 3, 110, 235, 207, filled=True)
    fonts[1].draw(42, 112, f'SOURCE {frame.width}x{frame.height}   SCALE {scale:.2f}x', (245, 199, 111))


def capture_canvas(p, path):
    # SDL 렌더러의 실제 결과를 읽어 smoke test의 시각 검증에 사용한다.
    import ctypes
    surface = p.SDL_CreateRGBSurfaceWithFormat(0, WINDOW_WIDTH, WINDOW_HEIGHT,
                                               32, p.SDL_PIXELFORMAT_ARGB8888)
    if not surface:
        raise RuntimeError('Unable to allocate a screenshot surface')
    try:
        result = p.SDL_RenderReadPixels(p.renderer, None, surface.contents.format.contents.format,
                                      surface.contents.pixels, surface.contents.pitch)
        if result != 0:
            raise RuntimeError('Unable to read the rendered canvas')
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        if p.SDL_SaveBMP(surface, str(path).encode('utf-8')) != 0:
            raise RuntimeError('Unable to save the rendered canvas')
    finally:
        p.SDL_FreeSurface(surface)


def run_viewer(smoke_seconds=None, screenshot=None):
    import pico2d as p
    data, animations = load_manifest()
    validate_manifest(data, animations)
    p.open_canvas(WINDOW_WIDTH, WINDOW_HEIGHT)
    try:
        sheet = load_sheet(p, data)
        fonts = load_ui_fonts(p)
        player = Playback(animations)
        running = True
        suspended = False
        show_bounds = False
        previous = started = time.perf_counter()
        captured = False
        while running:
            now = time.perf_counter()
            if not suspended:
                player.update(now - previous)
            previous = now
            if smoke_seconds is not None and now - started >= smoke_seconds:
                running = False
            for event in p.get_events():
                if event.type == p.SDL_QUIT or (event.type == p.SDL_KEYDOWN and event.key == p.SDLK_ESCAPE):
                    running = False
                elif event.type == p.SDL_KEYDOWN and event.key == p.SDLK_SPACE:
                    suspended = not suspended
                elif event.type == p.SDL_KEYDOWN and event.key == p.SDLK_b:
                    show_bounds = not show_bounds
                elif event.type == p.SDL_KEYDOWN and event.key == p.SDLK_r:
                    player = Playback(animations)
                    suspended = False
            if not running:
                break
            p.clear_canvas()
            draw_backdrop(p)
            draw_hud(p, fonts, player, suspended)
            draw_sequence(p, fonts, player)
            frame = player.animation.frames[player.frame_index]
            draw_frame(sheet, frame, WINDOW_WIDTH / 2, FLOOR_Y, display_scale(frame))
            if show_bounds:
                draw_bounds(p, fonts, sheet, frame, display_scale(frame))
            if screenshot and not captured:
                capture_canvas(p, screenshot)
                captured = True
            p.update_canvas()
            p.delay(0.005)
    finally:
        p.close_canvas()


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--smoke-seconds', type=float, help='Run an automated rendering check and exit')
    parser.add_argument('--screenshot', type=Path, help='Save the first rendered canvas to a BMP')
    parser.add_argument('--validate', action='store_true', help='Validate the atlas without opening a window')
    args = parser.parse_args()
    if args.smoke_seconds is not None and (not math.isfinite(args.smoke_seconds) or args.smoke_seconds <= 0):
        parser.error('--smoke-seconds must be finite and positive')
    if args.validate:
        data, animations = load_manifest()
        validate_manifest(data, animations)
        for action in animations:
            print(f'{action.label}: {len(action.frames)} frames, {play_seconds(action):.2f}s playback + 1.00s rest')
    else:
        run_viewer(args.smoke_seconds, args.screenshot)


if __name__ == '__main__':
    main()
