import game_framework
import play_mode
from pico2d import *

image = None


def init():
    global image
    image = load_image('title.png')


def finish():
    global image
    del image


def handle_events():
    for event in get_events():
        if event.type == SDL_QUIT:
            game_framework.quit()
            return
        if event.type == SDL_KEYDOWN:
            if event.key == SDLK_ESCAPE:
                game_framework.quit()
                return
            if event.key == SDLK_SPACE:
                game_framework.change_mode(play_mode)
                return


def update():
    pass


def render():
    clear_canvas()
    image.draw(400, 300)
    update_canvas()
