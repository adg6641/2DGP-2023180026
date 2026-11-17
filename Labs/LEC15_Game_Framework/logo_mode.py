import game_framework
import title_mode
from pico2d import *

image = None
running = True
logo_start_time = 0.0

def init():
    global image, running, logo_start_time

    image = load_image('tuk_credit.png')
    running = True
    logo_start_time = get_time()
    pass

def finish():
    global image
    del image
    pass

def update():
    global logo_start_time
    if get_time() - logo_start_time >= 2.0:
        game_framework.change_mode(title_mode)
    pass

def render():
    clear_canvas()
    image.draw(400, 300)
    update_canvas()

def handle_events():
    events = get_events()