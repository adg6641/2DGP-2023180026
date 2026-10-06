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


def event_requests_exit(event, p):
    return event.type == p.SDL_QUIT or (
        event.type == p.SDL_KEYDOWN and event.key == p.SDLK_ESCAPE)


def run_viewer(smoke_seconds=None):
    import pico2d as p

    p.open_canvas(WINDOW_WIDTH, WINDOW_HEIGHT)
    try:
        sheet = load_sheet(p)
        started = time.perf_counter()
        while smoke_seconds is None or time.perf_counter() - started < smoke_seconds:
            if any(event_requests_exit(event, p) for event in p.get_events()):
                break
            p.clear_canvas()
            draw_frame(sheet, ANIMATIONS[0].frames[0])
            p.update_canvas()
            p.delay(0.005)
    finally:
        p.close_canvas()


def main():
    run_viewer()


if __name__ == '__main__':
    main()
