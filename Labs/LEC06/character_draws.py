# 실습 과제 진행
from pico2d import *

open_canvas(800, 600)

import math

character = load_image('character.png')

def draw_character(x, y):
    clear_canvas()
    character.draw(x, y)
    update_canvas()
    delay(0.01)

def draw_circle():
    print("CIRCLE")
    for deg in range(0, 360, 5):
        rad = math.radians(deg)
        x = 400 + 200 * math.cos(rad)
        y = 300 + 200 * math.sin(rad)
        draw_character(x, y)
    pass

def draw_rectangle():
    print("RECTANGLE")

def draw_triangle():
    print("TRIANGLE")

def draw_top():
    print("TOP")
    for x in range(50, 751, 5):
        draw_character(x, 550)

def draw_right():
    print("RIGHT")
    for y in range(550, 50, -5):
        draw_character(750, y)

def draw_bottom():
    print("BOTTOM")
    pass

while True:
    draw_circle()
    draw_rectangle()
    draw_triangle()

close_canvas()
