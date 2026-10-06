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
PANEL_LEFT = 160
PANEL_RIGHT = WINDOW_WIDTH - 160
PANEL_BOTTOM = 200
PANEL_TOP = WINDOW_HEIGHT - 96
MOVEMENT_MARGIN = 24
START_X = WINDOW_WIDTH / 2
GROUND_Y = WINDOW_HEIGHT / 2


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


@dataclass(frozen=True)
class Motion:
    speed: float = 0.0  # 확대된 화면의 픽셀/초
    jump_height: float = 0.0  # 확대된 화면의 픽셀
    frame_directions: tuple[int, ...] = ()  # 비어 있으면 원본은 오른쪽 방향


STATIC_MOTION = Motion()
MOTIONS = {
    'A01': Motion(speed=100),
    'A02': Motion(speed=220),
    'A03': Motion(speed=300),
    'A04': STATIC_MOTION,
    'A05': Motion(speed=180),
    'A06': Motion(speed=300),
    'A07': Motion(speed=380),
    'A08': Motion(speed=130, jump_height=80),
    'A09': Motion(speed=200, frame_directions=(1, 1, 1, 1, -1, -1, -1, -1)),
    'A10': STATIC_MOTION,
}


@dataclass(frozen=True)
class Placement:
    x: float
    y: float
    direction: int = 1
    flip: bool = False


def movement_bounds(animations):
    frames = [frame for action in animations for frame in action.frames]
    # 좌우 반전된 프레임도 동일한 안전 영역 안에 들어오게 한다.
    extent = max(max(frame.pivot_x, frame.width - frame.pivot_x)
                 for frame in frames) * SCALE
    left = PANEL_LEFT + MOVEMENT_MARGIN + extent
    right = PANEL_RIGHT - MOVEMENT_MARGIN - extent
    if not left < START_X < right:
        raise ValueError('확대된 프레임이 이동 관찰 영역에 들어오지 않습니다.')
    return left, right


def motion_distance(action, motion, seconds):
    if not motion.frame_directions:
        return seconds * motion.speed
    # A09처럼 원본에서 방향이 바뀌는 동작은 프레임별 방향을 시간으로 적분한다.
    cycles = math.floor(seconds / action.cycle_seconds)
    remainder = seconds - cycles * action.cycle_seconds
    signed_seconds = cycles * sum(motion.frame_directions) * action.frame_seconds
    signed_seconds += math.fsum(
        direction * min(action.frame_seconds, max(0.0, remainder - index * action.frame_seconds))
        for index, direction in enumerate(motion.frame_directions))
    return signed_seconds * motion.speed


def character_placement(player):
    action = player.animation
    motion = MOTIONS.get(action.id, STATIC_MOTION)
    if motion.speed == 0 and motion.jump_height == 0:
        return Placement(START_X, GROUND_Y)
    # 휴식 전체 구간에서 마지막 재생 시점의 위치·방향을 유지한다.
    seconds = min(player.elapsed, player.play_seconds)
    left, right = player.movement_bounds
    width = right - left
    phase = (START_X - left + motion_distance(action, motion, seconds)) % (2 * width)
    if phase < width:
        x, reflected = left + phase, 1
    else:
        x, reflected = right - (phase - width), -1
    native_direction = (motion.frame_directions[player.frame_index]
                        if motion.frame_directions else 1)
    y = GROUND_Y
    if motion.jump_height and not player.resting:
        jump_phase = (seconds % action.cycle_seconds) / action.cycle_seconds
        y += motion.jump_height * 4 * jump_phase * (1 - jump_phase)
    return Placement(x, y, native_direction * reflected, reflected < 0)


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
        motion = MOTIONS.get(action.id, STATIC_MOTION)
        if any(not math.isfinite(value) or value < 0
               for value in (motion.speed, motion.jump_height)):
            raise ValueError(f'{action.id}: 이동 속도와 점프 높이는 0 이상의 유한한 값이어야 합니다.')
        if motion.frame_directions and (len(motion.frame_directions) != len(action.frames)
                                       or any(value not in (-1, 1) for value in motion.frame_directions)):
            raise ValueError(f'{action.id}: 프레임별 방향은 프레임 수와 일치하는 -1 또는 1이어야 합니다.')
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
    image_dimensions(IMAGE_PATH)
    p.SDL_SetHint(b'SDL_RENDER_SCALE_QUALITY', b'0')
    try:
        sheet = p.load_image(str(IMAGE_PATH))
    except (OSError, ValueError) as error:
        raise ValueError(f'스프라이트 PNG 로딩에 실패했습니다: {IMAGE_PATH}') from error
    if sheet is None:
        raise ValueError(f'스프라이트 이미지 로딩에 실패했습니다: {IMAGE_PATH}')
    return sheet


def draw_backdrop(p):
    p.draw_rectangle(0, 0, WINDOW_WIDTH - 1, WINDOW_HEIGHT - 1,
                     229, 237, 246, filled=True)
    p.draw_rectangle(PANEL_LEFT, PANEL_BOTTOM, PANEL_RIGHT, PANEL_TOP,
                     247, 250, 253, filled=True)
    p.draw_rectangle(PANEL_LEFT, PANEL_BOTTOM, PANEL_RIGHT, PANEL_TOP,
                     187, 203, 221)
    # 정렬 기준선은 포즈 변화와 휴식 중 위치 고정을 관찰하는 데 사용한다.
    p.draw_rectangle(PANEL_LEFT + MOVEMENT_MARGIN, GROUND_Y - 1,
                     PANEL_RIGHT - MOVEMENT_MARGIN, GROUND_Y,
                     210, 223, 237, filled=True)


def draw_frame(sheet, frame, x=START_X, y=GROUND_Y, scale=SCALE, flip=False):
    pivot_x = frame.width - frame.pivot_x if flip else frame.pivot_x
    center_x = x + (frame.width / 2 - pivot_x) * scale
    center_y = y + (frame.pivot_y - frame.height / 2) * scale
    sheet.clip_composite_draw(*clip_rectangle(frame, sheet.h), 0, 'h' if flip else '',
                              center_x, center_y, frame.width * scale, frame.height * scale)


class Playback:
    def __init__(self, animations=ANIMATIONS):
        if not animations:
            raise ValueError('재생할 동작이 없습니다.')
        for action in animations:
            if not action.frames or not math.isfinite(action.frame_seconds) or action.frame_seconds <= TIME_EPSILON:
                raise ValueError(f'{action.id}: 프레임과 유효한 재생 시간이 필요합니다.')
        self.animations = animations
        self.animation_index = 0
        self.elapsed = 0.0
        self.movement_bounds = movement_bounds(animations)
        self.sequence_seconds = math.fsum(
            action.cycle_seconds * REPEAT_COUNT + REST_SECONDS for action in animations)

    @property
    def animation(self):
        return self.animations[self.animation_index]

    @property
    def frame_index(self):
        if self.finished:
            return len(self.animation.frames) - 1
        return int((self.elapsed + TIME_EPSILON) / self.animation.frame_seconds) % len(self.animation.frames)

    @property
    def play_seconds(self):
        return self.animation.cycle_seconds * REPEAT_COUNT

    @property
    def completed_repeats(self):
        return min(REPEAT_COUNT, int((self.elapsed + TIME_EPSILON) / self.animation.cycle_seconds))

    @property
    def finished(self):
        return self.elapsed + TIME_EPSILON >= self.play_seconds

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
        if not math.isfinite(seconds) or seconds < 0:
            raise ValueError('경과 시간은 0 이상의 유한한 값이어야 합니다.')
        self.elapsed += seconds
        # 여러 전체 순환을 넘는 지연도 동작 수에 비례하는 비용으로 처리한다.
        if self.elapsed >= self.sequence_seconds:
            self.elapsed %= self.sequence_seconds
        while self.elapsed + TIME_EPSILON >= self.play_seconds + REST_SECONDS:
            self.elapsed = max(0.0, self.elapsed - self.play_seconds - REST_SECONDS)
            self.animation_index = (self.animation_index + 1) % len(self.animations)


def validate_playback():
    """창을 열지 않고 반복·휴식·순환 경계와 시간 지연을 검증한다."""
    for action in ANIMATIONS:
        player = Playback((action,))
        for repeat in range(REPEAT_COUNT):
            player.elapsed = repeat * action.cycle_seconds
            assert player.frame_index == 0 and player.completed_repeats == repeat
            for index in range(len(action.frames)):
                player.elapsed = repeat * action.cycle_seconds + index * action.frame_seconds
                assert player.frame_index == index and not player.resting
        player.elapsed = player.play_seconds - 1e-6
        assert not player.resting and player.frame_index == len(action.frames) - 1
        player.update(1e-6)
        assert player.resting and player.completed_repeats == REPEAT_COUNT
        assert player.frame_index == len(action.frames) - 1
        assert math.isclose(player.rest_remaining, REST_SECONDS, abs_tol=TIME_EPSILON)
        player.update(REST_SECONDS - 1e-6)
        assert player.resting
        player.update(1e-6)
        assert player.frame_index == 0 and not player.resting
        assert math.isclose(player.elapsed, 0, abs_tol=TIME_EPSILON)

    player = Playback()
    for index, action in enumerate(ANIMATIONS):
        player.update(action.cycle_seconds * REPEAT_COUNT + REST_SECONDS)
        assert player.animation_index == (index + 1) % len(ANIMATIONS)
        assert player.frame_index == 0 and player.completed_repeats == 0

    whole, split = Playback(), Playback()
    whole.update(whole.sequence_seconds * 3 + 7.35)
    for _ in range(100):
        split.update((split.sequence_seconds * 3 + 7.35) / 100)
    assert whole.animation_index == split.animation_index == 1
    assert whole.frame_index == split.frame_index
    assert math.isclose(whole.elapsed, split.elapsed, abs_tol=TIME_EPSILON)
    assert math.isclose(whole.elapsed, 0.85, abs_tol=TIME_EPSILON)

    single = Animation('SINGLE', '단일 포즈', (ANIMATIONS[0].frames[0],))
    player = Playback((single,))
    player.update(0.5)
    assert player.resting and player.frame_index == 0 and player.completed_repeats == 5
    player.update(1.0)
    assert not player.resting and player.completed_repeats == 0
    for invalid in (-1, math.nan, math.inf):
        try:
            player.update(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError('잘못된 경과 시간이 허용되었습니다.')
    print('시간 검증 완료: 전체 프레임, 5회 반복, 1초 휴식, 순환, 지연, 단일 포즈')


def validate_movement():
    """이동·반사·방향·점프·휴식과 프레임 속도 독립성을 검증한다."""
    moving = {'A01', 'A02', 'A03', 'A05', 'A06', 'A07', 'A08', 'A09'}
    for index, action in enumerate(ANIMATIONS):
        player = Playback()
        player.animation_index = index
        start = character_placement(player)
        player.update(0.04)
        assert player.frame_index == 0
        position = character_placement(player)
        if action.id in moving:
            assert position.x > start.x
        else:
            assert position == start == Placement(START_X, GROUND_Y)

        # 모든 동작의 전체 재생 구간에서 반전된 프레임과 점프도 잘리지 않는다.
        for sample in range(201):
            player.elapsed = player.play_seconds * sample / 200
            position = character_placement(player)
            frame = action.frames[player.frame_index]
            pivot_x = frame.width - frame.pivot_x if position.flip else frame.pivot_x
            left = position.x - pivot_x * SCALE
            right = left + frame.width * SCALE
            top = position.y + frame.pivot_y * SCALE
            bottom = top - frame.height * SCALE
            assert PANEL_LEFT <= left <= right <= PANEL_RIGHT
            assert PANEL_BOTTOM <= bottom <= top <= PANEL_TOP
        player.elapsed = player.play_seconds
        final = character_placement(player)
        player.update(0.99)
        assert player.resting and character_placement(player) == final
        player.update(0.01)
        assert player.frame_index == 0
        assert character_placement(player) == Placement(START_X, GROUND_Y)

    player = Playback()
    player.animation_index = 1  # 달리기: 오른쪽 경계와 왼쪽 경계에서 각각 반사
    left, right = player.movement_bounds
    speed = MOTIONS['A02'].speed
    hit_right = (right - START_X) / speed
    hit_left = hit_right + (right - left) / speed
    for boundary_time, expected_direction in ((hit_right, -1), (hit_left, 1)):
        player.elapsed = boundary_time - 1e-6
        before = character_placement(player)
        player.elapsed = boundary_time + 1e-6
        after = character_placement(player)
        assert before.direction == -expected_direction and after.direction == expected_direction
        assert after.flip == (expected_direction < 0)
        assert abs(before.x - after.x) < 1e-6

    player.animation_index = 8  # 원본 A09의 오른쪽→왼쪽 방향 전환
    player.elapsed = 0.2
    before = character_placement(player)
    player.elapsed = 0.6
    after = character_placement(player)
    assert before.direction == 1 and after.direction == -1
    assert not before.flip and not after.flip
    assert math.isclose(before.x, after.x, abs_tol=TIME_EPSILON)
    player.elapsed = player.animation.cycle_seconds
    assert math.isclose(character_placement(player).x, START_X, abs_tol=TIME_EPSILON)

    player.animation_index = 7
    player.elapsed = player.animation.cycle_seconds / 2
    assert math.isclose(character_placement(player).y, GROUND_Y + MOTIONS['A08'].jump_height)
    player.elapsed = player.animation.cycle_seconds
    assert math.isclose(character_placement(player).y, GROUND_Y)
    player.elapsed = player.play_seconds
    assert character_placement(player).y == GROUND_Y

    whole, split = Playback(), Playback()
    whole.update(48 * 3 + 7.35)
    for _ in range(100):
        split.update((48 * 3 + 7.35) / 100)
    a, b = character_placement(whole), character_placement(split)
    assert math.isclose(a.x, b.x, abs_tol=TIME_EPSILON)
    assert math.isclose(a.y, b.y, abs_tol=TIME_EPSILON)
    assert (a.direction, a.flip) == (b.direction, b.flip)
    print('이동 검증 완료: 8개 이동, 2개 제자리, 경계·반전, 방향 전환, 점프, 휴식, 지연')


def status_text(player):
    action = player.animation
    repeat = REPEAT_COUNT if player.resting else player.completed_repeats + 1
    state = f'휴식 {player.rest_remaining:.2f}초' if player.resting else '재생'
    placement = character_placement(player)
    direction = '오른쪽' if placement.direction > 0 else '왼쪽'
    return (f'{action.id} {action.name} | 프레임 {player.frame_index + 1}/{len(action.frames)}'
            f' | 반복 {repeat}/{REPEAT_COUNT} | {state}'
            f' | 위치 ({placement.x:.0f}, {placement.y:.0f}) {direction}')


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
            draw_backdrop(p)
            placement = character_placement(player)
            draw_frame(sheet, player.animation.frames[player.frame_index],
                       placement.x, placement.y, flip=placement.flip)
            p.update_canvas()
            p.delay(0.005)
    finally:
        p.close_canvas()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validate', action='store_true', help='창을 열지 않고 프레임 데이터 검증')
    parser.add_argument('--self-test', action='store_true', help='창을 열지 않고 재생 시간과 이동 검증')
    parser.add_argument('--smoke-seconds', type=float, help='지정한 초 뒤 자동 종료')
    args = parser.parse_args()
    try:
        if args.validate or args.self_test:
            validate_animations(ANIMATIONS, image_dimensions())
            if args.validate:
                for action in ANIMATIONS:
                    print(f'{action.id} {action.name}: {len(action.frames)}프레임')
                print(f'검증 완료: {len(ANIMATIONS)}개 동작, '
                      f'{sum(len(action.frames) for action in ANIMATIONS)}프레임')
            if args.self_test:
                validate_playback()
                validate_movement()
        else:
            run_viewer(args.smoke_seconds)
    except (OSError, ValueError, ImportError) as error:
        print(f'실행 오류: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
