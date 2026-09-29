# 실습 과제 진행
from pico2d import *

open_canvas(800, 600)

character = load_image('character.png')

def draw_character(x, y):
    clear_canvas()
    character.draw(x, y)
    update_canvas()
    delay(0.01)

def draw_circle():
    pass

def draw_rectangle():
    pass

def draw_triangle():
    pass

while True:
    pass

close_canvas()
