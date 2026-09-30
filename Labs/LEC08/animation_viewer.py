"""Drill #8: a metadata-driven pico2d sprite animation viewer."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def main():
    import pico2d as p
    p.open_canvas(960, 640)
    try:
        p.clear_canvas()
        p.update_canvas()
        p.delay(0.2)
    finally:
        p.close_canvas()


if __name__ == '__main__':
    main()
