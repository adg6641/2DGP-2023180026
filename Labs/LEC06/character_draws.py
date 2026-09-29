# 실습 과제 진행
from pico2d import *

open_canvas(800, 600)

character = load_image('character.png')

def draw_character(x, y):
    clear_canvas()
    character.draw(x, y)
    update_canvas()
    delay(0.01)

clear_canvas()
character.draw(400, 300)
update_canvas()
delay(1)
close_canvas()
