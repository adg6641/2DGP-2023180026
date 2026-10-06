"""소닉 스프라이트 시트의 모든 동작을 자동 재생하는 pico2d 뷰어."""

import time

WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
SCALE = 4
REPEAT_COUNT = 5
REST_SECONDS = 1.0
FRAME_SECONDS = 0.1


def run_viewer(smoke_seconds=None):
    import pico2d as p

    p.open_canvas(WINDOW_WIDTH, WINDOW_HEIGHT)
    try:
        started = time.perf_counter()
        while smoke_seconds is None or time.perf_counter() - started < smoke_seconds:
            p.clear_canvas()
            p.update_canvas()
            p.delay(0.005)
    finally:
        p.close_canvas()


def main():
    run_viewer()


if __name__ == '__main__':
    main()
