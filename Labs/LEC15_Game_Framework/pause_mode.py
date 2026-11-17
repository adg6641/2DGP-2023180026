import game_framework
import game_world
from pico2d import *

font = None


def init():
    global font
    font = load_font('C:/Windows/Fonts/arial.ttf', 32)


def finish():
    global font
    del font


def handle_events():
    for event in get_events():
        if event.type == SDL_QUIT:
            game_framework.quit()
            return
        if event.type == SDL_KEYDOWN and event.key == SDLK_p:
            game_framework.pop_mode()
            return


def update():
    pass


def render():
    clear_canvas()
    game_world.render()
    font.draw(340, 330, 'PAUSED', (255, 255, 255))
    font.draw(270, 280, 'Press P to resume', (255, 255, 255))
    update_canvas()
