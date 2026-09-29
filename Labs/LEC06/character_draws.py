# 실습 과제 진행
from pico2d import *


open_canvas(800, 600)


character = load_image('character.png')


def draw_circle():
    print("CIRCLE")
    for deg in range(0, 360, 5):
        rad = math.radians(deg)
        x = 400 + 200 * math.cos(rad)
        y = 300 + 200 * math.sin(rad)
        draw_character(x, y)
    pass


def draw_top():
    print("TOP")
    for x in range(50, 750, 5):
        draw_character(x, 550)


def draw_character(x, y):
    clear_canvas()
    character.draw(x, y)
    update_canvas()
    delay(0.01)


def draw_right():
    print("RIGHT")
    for y in range(550, 50, -5):
        draw_character(750, y)


def draw_bottom():
    print("BOTTOM")
    for x in range(750, 50, -5):
        draw_character(x, 50)


def draw_left():
    print("LEFT")
    for y in range(50, 550, 5):
        draw_character(50, y)


def draw_rectangle():
    print("RECTANGLE")
    draw_top()
    draw_right()
    draw_bottom()
    draw_left()
    pass


def draw_triangle_bottom():
    print("TRIANGLE_BOTTOM")
    for x in range(100, 700, 5):
        draw_character(x, 100)


def draw_triangle_right():
    print("TRIANGLE_RIGHT")
    n = 100
    for step in range(n + 1):
        t = step / n
        x = 700 + (400 - 700) * t
        y = 100 + (500 - 100) * t
        draw_character(x, y)


def draw_triangle_left():
    print("TRIANGLE_LEFT")
    n = 100
    for step in range(n + 1):
        t = step / n
        x = 400 + (100 - 400) * t
        y = 500 + (100 - 500) * t
        draw_character(x, y)


def draw_triangle():
    print("TRIANGLE")
    draw_triangle_bottom()
    draw_triangle_right()
    draw_triangle_left()


while True:
    draw_circle()
    draw_rectangle()
    draw_triangle()


close_canvas()