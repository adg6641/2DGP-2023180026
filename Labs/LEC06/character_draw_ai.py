from pico2d import *
import math


WIDTH = 800
HEIGHT = 600

SPEED = 500.0
TARGET_FPS = 120
FRAME_TIME = 1.0 / TARGET_FPS

running = True


open_canvas(WIDTH, HEIGHT)

character = load_image('character.png')


# --------------------------------------------------
# 원 설정
# --------------------------------------------------
CIRCLE_X = 400
CIRCLE_Y = 300
CIRCLE_RADIUS = 200

circle_angle = 0.0


# --------------------------------------------------
# 사각형 경로
# --------------------------------------------------
rectangle_points = [
    (50, 550),
    (750, 550),
    (750, 50),
    (50, 50),
    (50, 550)
]


# --------------------------------------------------
# 삼각형 경로
# --------------------------------------------------
triangle_points = [
    (100, 100),
    (700, 100),
    (400, 500),
    (100, 100)
]


state = "CIRCLE"

path_index = 0

x = CIRCLE_X + CIRCLE_RADIUS
y = CIRCLE_Y


# --------------------------------------------------
# 이벤트 처리
# --------------------------------------------------
def handle_events():
    global running

    for event in get_events():

        if event.type == SDL_QUIT:
            running = False

        elif event.type == SDL_KEYDOWN:

            if event.key == SDLK_ESCAPE:
                running = False


# --------------------------------------------------
# 직선 경로 이동
# --------------------------------------------------
def move_line(points, distance):
    global x, y
    global path_index

    while distance > 0:

        if path_index >= len(points) - 1:
            return distance, True

        target_x, target_y = points[path_index + 1]

        dx = target_x - x
        dy = target_y - y

        remain_distance = math.sqrt(dx * dx + dy * dy)

        if remain_distance == 0:
            path_index += 1
            continue

        if distance < remain_distance:

            ratio = distance / remain_distance

            x += dx * ratio
            y += dy * ratio

            distance = 0

        else:

            x = target_x
            y = target_y

            distance -= remain_distance

            path_index += 1

    return distance, False


# --------------------------------------------------
# 캐릭터 위치 갱신
# --------------------------------------------------
def update_character(dt):
    global state
    global circle_angle
    global path_index
    global x, y

    move_distance = SPEED * dt

    while move_distance > 0:

        # ------------------------------
        # 원
        # ------------------------------
        if state == "CIRCLE":

            remain_angle = 2.0 * math.pi - circle_angle
            remain_distance = remain_angle * CIRCLE_RADIUS

            if move_distance < remain_distance:

                circle_angle += move_distance / CIRCLE_RADIUS

                x = CIRCLE_X + CIRCLE_RADIUS * math.cos(circle_angle)
                y = CIRCLE_Y + CIRCLE_RADIUS * math.sin(circle_angle)

                move_distance = 0

            else:

                move_distance -= remain_distance

                state = "RECTANGLE"
                path_index = 0

                x, y = rectangle_points[0]

        # ------------------------------
        # 사각형
        # ------------------------------
        elif state == "RECTANGLE":

            move_distance, finished = move_line(
                rectangle_points,
                move_distance
            )

            if finished:

                state = "TRIANGLE"
                path_index = 0

                x, y = triangle_points[0]

        # ------------------------------
        # 삼각형
        # ------------------------------
        elif state == "TRIANGLE":

            move_distance, finished = move_line(
                triangle_points,
                move_distance
            )

            if finished:

                state = "CIRCLE"

                circle_angle = 0.0

                x = CIRCLE_X + CIRCLE_RADIUS
                y = CIRCLE_Y


# --------------------------------------------------
# 화면 출력
# --------------------------------------------------
def draw_character():
    clear_canvas()

    character.draw(x, y)

    update_canvas()


# --------------------------------------------------
# 메인 루프
# --------------------------------------------------
previous_time = get_time()


while running:

    frame_start = get_time()

    handle_events()

    current_time = get_time()

    dt = current_time - previous_time
    previous_time = current_time

    # 창 이동 등으로 너무 긴 시간이 지나간 경우
    # 캐릭터가 갑자기 멀리 점프하는 것을 방지
    if dt > 0.05:
        dt = 0.05

    update_character(dt)

    draw_character()

    frame_used_time = get_time() - frame_start
    remain_time = FRAME_TIME - frame_used_time

    if remain_time > 0:
        delay(remain_time)


close_canvas()