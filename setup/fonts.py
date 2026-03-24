import pygame as py
from setup.files import FONT_DIR

py.font.init()

def load_font(name, size):
    path = FONT_DIR / name
    if not path.exists():
        return None
    
    custom_font = py.font.Font(path, size)
    return custom_font

TITLE_FONT_SIZE = 60
LABEL_FONT_SIZE = 40
SIDEBAR_FONT_SIZE = 25
I_O_LABEL_FONT_SIZE = 15

BUTTON_FONT_SIZE = 30
SMALL_BUTTON_FONT_SIZE = 28

TITLE_FONT = py.font.SysFont("Arial", TITLE_FONT_SIZE)
LABEL_FONT = load_font("grityle.ttf", LABEL_FONT_SIZE)
IO_FONT = py.font.SysFont("Arial", I_O_LABEL_FONT_SIZE)
SIDEBAR_FONT = py.font.SysFont("Arial", SIDEBAR_FONT_SIZE)

TITLE_HEIGHT = TITLE_FONT.get_height()
LABEL_HEIGHT = LABEL_FONT.get_height()

PAUSE_TITLE = TITLE_FONT.render("Paused", True, (255, 255, 255))

def get_offset(font):
    ascent = font.get_ascent()
    descent = abs(font.get_descent())
    offset = (ascent - descent) // 2

    return offset

block_font_offset = get_offset(LABEL_FONT)