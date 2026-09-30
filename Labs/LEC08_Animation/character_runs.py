from pico2d import *

open_canvas()

grass = load_image('grass.png')
character = load_image('run_animation.png')

frame = 0

for x in range(0, 800, 5):
    clear_canvas()
    grass.draw(400, 30)
    character.clip_composite_draw(
        frame * 100, 0, # left, bottom
        100, 100, # width, height
        math.pi/4,'h', # rotation, scale
        x, 90, # destination x, y
        200, 200 # width, height
    )
    update_canvas()

    frame = (frame + 1) % 8
    delay(0.05)

close_canvas()

