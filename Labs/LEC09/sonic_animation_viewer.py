"""소닉 스프라이트 시트의 모든 동작을 자동 재생하는 pico2d 뷰어."""

import time
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
IMAGE_PATH = BASE_DIR / 'sonic-sprite.png'

WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
SCALE = 4
REPEAT_COUNT = 5
REST_SECONDS = 1.0
FRAME_SECONDS = 0.1
TIME_EPSILON = 1e-9


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
    id: str
    name: str
    frames: tuple[Frame, ...]
    frame_seconds: float = FRAME_SECONDS

    @property
    def cycle_seconds(self):
        return len(self.frames) * self.frame_seconds


def frames_from_rectangles(rectangles, baseline):
    # 행의 공통 기준선을 보존하여 원본 포즈의 상하 변화를 유지한다.
    return tuple(Frame(x, y, w, h, w / 2, baseline - y)
                 for x, y, w, h in rectangles)


ANIMATIONS = (
    Animation('A01', '걷기와 회전', frames_from_rectangles((
        (1, 39, 29, 39), (31, 40, 26, 38), (58, 39, 28, 39),
        (86, 40, 30, 38), (118, 40, 30, 38), (150, 40, 30, 38),
        (182, 40, 29, 38), (211, 39, 29, 38), (240, 39, 29, 38),
        (270, 45, 24, 32), (302, 51, 29, 26),
    ), 78)),
    Animation('A02', '달리기', frames_from_rectangles((
        (8, 80, 26, 37), (37, 80, 27, 37), (65, 80, 31, 38),
        (97, 80, 37, 37), (135, 80, 32, 35), (170, 79, 32, 38),
        (206, 79, 26, 38), (238, 80, 24, 37), (263, 80, 30, 37),
        (295, 80, 36, 37), (334, 80, 32, 36), (370, 79, 29, 38),
    ), 118)),
    Animation('A03', '전력 질주', frames_from_rectangles((
        (1, 124, 33, 40), (39, 124, 35, 39), (89, 125, 35, 38),
        (130, 121, 34, 42), (181, 122, 34, 41), (228, 122, 33, 40),
    ), 164)),
    Animation('A04', '회전 진입', frames_from_rectangles((
        (1, 169, 29, 30), (35, 167, 29, 31), (67, 169, 30, 29),
        (98, 169, 31, 29), (131, 168, 29, 30), (162, 168, 29, 31),
        (193, 170, 30, 29), (230, 170, 31, 29), (268, 170, 30, 30),
    ), 200)),
    Animation('A05', '구르기', frames_from_rectangles((
        (1, 206, 30, 27), (36, 206, 29, 27), (70, 206, 29, 27),
        (105, 206, 29, 27), (139, 206, 29, 27), (174, 206, 29, 27),
    ), 233)),
    Animation('A06', '고속 달리기', frames_from_rectangles((
        (1, 239, 29, 35), (36, 239, 30, 35), (74, 239, 31, 35),
        (111, 238, 31, 36), (149, 239, 30, 35), (186, 238, 31, 36),
    ), 274)),
)


def clip_rectangle(frame, image_height):
    # 데이터는 왼쪽 위 원점, pico2d의 크롭 좌표는 왼쪽 아래 원점이다.
    return frame.x, image_height - frame.y - frame.height, frame.width, frame.height


def load_sheet(p):
    p.SDL_SetHint(b'SDL_RENDER_SCALE_QUALITY', b'0')
    return p.load_image(str(IMAGE_PATH))


def draw_frame(sheet, frame, x=WINDOW_WIDTH / 2, y=WINDOW_HEIGHT / 2,
               scale=SCALE):
    center_x = x + (frame.width / 2 - frame.pivot_x) * scale
    center_y = y + (frame.pivot_y - frame.height / 2) * scale
    sheet.clip_draw(*clip_rectangle(frame, sheet.h), center_x, center_y,
                    frame.width * scale, frame.height * scale)


class Playback:
    def __init__(self, animations=ANIMATIONS):
        self.animations = animations
        self.animation_index = 0
        self.elapsed = 0.0

    @property
    def animation(self):
        return self.animations[self.animation_index]

    @property
    def frame_index(self):
        if self.finished:
            return len(self.animation.frames) - 1
        return int(self.elapsed / self.animation.frame_seconds) % len(self.animation.frames)

    @property
    def play_seconds(self):
        return self.animation.cycle_seconds * REPEAT_COUNT

    @property
    def completed_repeats(self):
        return min(REPEAT_COUNT, int(self.elapsed / self.animation.cycle_seconds))

    @property
    def finished(self):
        return self.elapsed >= self.play_seconds

    @property
    def resting(self):
        return self.finished

    @property
    def state(self):
        return 'RESTING' if self.resting else 'PLAYING'

    @property
    def rest_remaining(self):
        return max(0.0, self.play_seconds + REST_SECONDS - self.elapsed)

    def update(self, seconds):
        self.elapsed += seconds
        if self.elapsed + TIME_EPSILON >= self.play_seconds + REST_SECONDS:
            self.animation_index = (self.animation_index + 1) % len(self.animations)
            self.elapsed = 0.0


def event_requests_exit(event, p):
    return event.type == p.SDL_QUIT or (
        event.type == p.SDL_KEYDOWN and event.key == p.SDLK_ESCAPE)


def run_viewer(smoke_seconds=None):
    import pico2d as p

    p.open_canvas(WINDOW_WIDTH, WINDOW_HEIGHT)
    try:
        sheet = load_sheet(p)
        player = Playback()
        previous = started = time.perf_counter()
        while smoke_seconds is None or time.perf_counter() - started < smoke_seconds:
            if any(event_requests_exit(event, p) for event in p.get_events()):
                break
            now = time.perf_counter()
            player.update(now - previous)
            previous = now
            p.clear_canvas()
            draw_frame(sheet, player.animation.frames[player.frame_index])
            p.update_canvas()
            p.delay(0.005)
    finally:
        p.close_canvas()


def main():
    run_viewer()


if __name__ == '__main__':
    main()
