"""소닉 스프라이트 시트의 모든 동작을 자동 재생하는 pico2d 뷰어."""

import argparse
import math
import struct
import sys
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
    Animation('A07', '초고속 달리기', frames_from_rectangles((
        (1, 283, 29, 35), (36, 283, 30, 35), (72, 286, 39, 31),
        (123, 285, 39, 32), (172, 286, 39, 31), (218, 285, 38, 32),
    ), 318)),
    Animation('A08', '회전과 공중 포즈', frames_from_rectangles((
        (1, 326, 24, 45), (31, 327, 29, 44), (65, 327, 20, 44),
        (90, 327, 25, 43), (119, 327, 25, 43), (149, 327, 20, 44),
        (184, 341, 40, 28), (232, 341, 39, 27),
    ), 371)),
    Animation('A09', '방향 전환 달리기', frames_from_rectangles((
        (1, 379, 27, 38), (31, 379, 31, 36), (64, 379, 31, 36),
        (99, 377, 33, 38), (136, 379, 32, 36), (176, 379, 33, 36),
        (217, 379, 33, 36), (254, 378, 33, 36),
    ), 417)),
    Animation('A10', '손들기와 대기 포즈', frames_from_rectangles((
        (6, 429, 34, 40), (49, 426, 34, 43),
        (96, 427, 23, 39), (125, 427, 23, 39),
    ), 469)),
)


def clip_rectangle(frame, image_height):
    # 데이터는 왼쪽 위 원점, pico2d의 크롭 좌표는 왼쪽 아래 원점이다.
    return frame.x, image_height - frame.y - frame.height, frame.width, frame.height


def image_dimensions(path=IMAGE_PATH):
    if not path.is_file():
        raise FileNotFoundError(f'스프라이트 이미지를 찾을 수 없습니다: {path}')
    with path.open('rb') as source:
        header = source.read(24)
    if len(header) != 24 or header[:8] != b'\x89PNG\r\n\x1a\n' or header[12:16] != b'IHDR':
        raise ValueError(f'올바른 PNG 이미지가 아닙니다: {path}')
    return struct.unpack('>II', header[16:24])


def validate_animations(animations, image_size):
    if not animations:
        raise ValueError('재생할 동작이 없습니다.')
    image_width, image_height = image_size
    if min(image_width, image_height) <= 0:
        raise ValueError('이미지 크기는 양수여야 합니다.')
    if len({action.id for action in animations}) != len(animations):
        raise ValueError('동작 ID가 중복되었습니다.')
    for action in animations:
        if not action.id or not action.name or not action.frames:
            raise ValueError('동작에는 ID, 이름과 프레임이 필요합니다.')
        if not math.isfinite(action.frame_seconds) or action.frame_seconds <= TIME_EPSILON:
            raise ValueError(f'{action.id}: 프레임 시간은 {TIME_EPSILON}초보다 커야 합니다.')
        for index, frame in enumerate(action.frames, 1):
            prefix = f'{action.id} 프레임 {index}'
            if any(type(value) is not int for value in
                   (frame.x, frame.y, frame.width, frame.height)):
                raise ValueError(f'{prefix}: 크롭 좌표와 크기는 정수여야 합니다.')
            if min(frame.x, frame.y) < 0 or min(frame.width, frame.height) <= 0:
                raise ValueError(f'{prefix}: 크롭 좌표 또는 크기가 잘못되었습니다.')
            if frame.x + frame.width > image_width or frame.y + frame.height > image_height:
                raise ValueError(f'{prefix}: 크롭 영역이 이미지 밖에 있습니다.')
            # 공통 행 기준선은 작은 프레임의 크롭 영역 밖에 있을 수 있다.
            if not (math.isfinite(frame.pivot_x) and math.isfinite(frame.pivot_y)
                    and 0 <= frame.pivot_x <= frame.width
                    and 0 <= frame.pivot_y <= image_height):
                raise ValueError(f'{prefix}: 정렬 기준점이 잘못되었습니다.')


def load_sheet(p):
    image_dimensions()
    p.SDL_SetHint(b'SDL_RENDER_SCALE_QUALITY', b'0')
    sheet = p.load_image(str(IMAGE_PATH))
    if sheet is None:
        raise ValueError(f'스프라이트 이미지 로딩에 실패했습니다: {IMAGE_PATH}')
    return sheet


def draw_frame(sheet, frame, x=WINDOW_WIDTH / 2, y=WINDOW_HEIGHT / 2,
               scale=SCALE):
    center_x = x + (frame.width / 2 - frame.pivot_x) * scale
    center_y = y + (frame.pivot_y - frame.height / 2) * scale
    sheet.clip_draw(*clip_rectangle(frame, sheet.h), center_x, center_y,
                    frame.width * scale, frame.height * scale)


class Playback:
    def __init__(self, animations=ANIMATIONS):
        if not animations:
            raise ValueError('재생할 동작이 없습니다.')
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


def status_text(player):
    action = player.animation
    repeat = REPEAT_COUNT if player.resting else player.completed_repeats + 1
    state = f'휴식 {player.rest_remaining:.2f}초' if player.resting else '재생'
    return (f'{action.id} {action.name} | 프레임 {player.frame_index + 1}/{len(action.frames)}'
            f' | 반복 {repeat}/{REPEAT_COUNT} | {state}')


def report_status(player, p, window, previous_key):
    text = status_text(player)
    p.SDL_SetWindowTitle(window, f'소닉 애니메이션 뷰어 | {text} | ESC 종료'.encode('utf-8'))
    key = (player.animation_index, player.completed_repeats, player.state)
    if key != previous_key:
        print(text, flush=True)
    return key


def event_requests_exit(event, p):
    return event.type == p.SDL_QUIT or (
        event.type == p.SDL_KEYDOWN and event.key == p.SDLK_ESCAPE)


def run_viewer(smoke_seconds=None):
    if smoke_seconds is not None and (not math.isfinite(smoke_seconds) or smoke_seconds <= 0):
        raise ValueError('자동 종료 시간은 양의 유한한 값이어야 합니다.')
    import pico2d as p
    import pico2d.pico2d as backend

    p.open_canvas(WINDOW_WIDTH, WINDOW_HEIGHT)
    try:
        sheet = load_sheet(p)
        validate_animations(ANIMATIONS, (sheet.w, sheet.h))
        player = Playback()
        previous_status = None
        previous = started = time.perf_counter()
        while smoke_seconds is None or time.perf_counter() - started < smoke_seconds:
            if any(event_requests_exit(event, p) for event in p.get_events()):
                break
            now = time.perf_counter()
            player.update(now - previous)
            previous = now
            previous_status = report_status(player, p, backend.window, previous_status)
            p.clear_canvas()
            draw_frame(sheet, player.animation.frames[player.frame_index])
            p.update_canvas()
            p.delay(0.005)
    finally:
        p.close_canvas()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validate', action='store_true', help='창을 열지 않고 프레임 데이터 검증')
    parser.add_argument('--smoke-seconds', type=float, help='지정한 초 뒤 자동 종료')
    args = parser.parse_args()
    try:
        if args.validate:
            validate_animations(ANIMATIONS, image_dimensions())
            for action in ANIMATIONS:
                print(f'{action.id} {action.name}: {len(action.frames)}프레임')
            print(f'검증 완료: {len(ANIMATIONS)}개 동작, '
                  f'{sum(len(action.frames) for action in ANIMATIONS)}프레임')
        else:
            run_viewer(args.smoke_seconds)
    except (OSError, ValueError, ImportError) as error:
        print(f'실행 오류: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
