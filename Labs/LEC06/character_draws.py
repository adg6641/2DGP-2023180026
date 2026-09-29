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

def draw_rectangle():
    print("RECTANGLE")

def draw_triangle():
    print("TRIANGLE")

while True:
    draw_circle()
    draw_rectangle()
    draw_triangle()

close_canvas()
