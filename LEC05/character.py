from pico2d import *

open_canvas(800, 600)

character = load_image('character.png')
grass = load_image('grass.png')

x = 100
y = 90
direction = 0

while True:
    clear_canvas()
    grass.draw(400, 30)
    character.draw(x, y)
    update_canvas()
    delay(0.001)

    # 오른쪽
    if direction == 0:
        x += 1
        if x >= 700:
            direction = 1

    # 위쪽
    elif direction == 1:
        y += 1
        if y >= 500:
            direction = 2

    # 왼쪽
    elif direction == 2:
        x -= 1
        if x <= 100:
            direction = 3

    # 아래쪽
    elif direction == 3:
        y -= 1
        if y <= 90:
            direction = 0

delay(10)
close_canvas()
