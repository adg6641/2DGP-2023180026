from pico2d import *
import math

open_canvas(800, 600)

character = load_image('character.png')
grass = load_image('grass.png')

center_x = 400
center_y = 300

radius = 200
angle = 0

while True:
    x = center_x + radius * math.cos(angle)
    y = center_y + radius * math.sin(angle)

    clear_canvas()
    grass.draw(400, 30)
    character.draw(x, y)
    update_canvas()
    delay(0.001)

    angle += 0.01

    if angle >= 2 * math.pi:
        angle = 0

close_canvas()