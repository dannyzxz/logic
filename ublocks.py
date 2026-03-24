import pygame as py

from setup.fonts import LABEL_FONT, block_font_offset
from setup.colors import WHITE, DARK_GRAY, RED, ORANGE, YELLOW, GREEN, BLUE, INDIGO, VIOLET
from setup.widgets import BLOCK_WIDTH, BLOCK_HEIGHT

from block import Block

class Switch(Block):
    LABEL = "Switch"
    INPUTS = 0
    OUTPUTS = 1

    def __init__(self, pos, in_macro=False):
        super().__init__(pos, in_macro)
        self.on = False

    def on_click(self):
        self.on = not self.on

    def update_logic(self):
        self.outputs[0].value = self.on

    def get_state(self):
        return {"on": self.on}

    def set_state(self, state):
        if state:
            self.on = state.get("on", False)

class Button(Block):
    LABEL = "Button"
    INPUTS = 0
    OUTPUTS = 1

    def __init__(self, pos, in_macro=False):
        super().__init__(pos, in_macro)
        self.pressed = False

    def on_click(self):
        self.pressed = True

    def update_logic(self):
        if self.pressed and not py.mouse.get_pressed()[0]:
            self.pressed = False

        self.outputs[0].value = self.pressed

class Power(Block):
    LABEL = "Power"
    INPUTS = 0
    OUTPUTS = 1

    def __init__(self, pos, in_macro=False):
        super().__init__(pos, in_macro)
        self.outputs[0].value = True

class Clock(Block):
    LABEL = "Clock"
    INPUTS = 0
    OUTPUTS = 1

    def __init__(self, pos, in_macro=False):
        super().__init__(pos, in_macro)
        self.intervals = [100, 250, 500, 1000] 
        self.index = 3

        self.last_toggle = py.time.get_ticks()
        self.powered = False

        self.update_text()

    @property
    def interval(self):
        return self.intervals[self.index]
    
    def update_text(self):
        block_rect = self.image.get_rect()

        label1 = "Clock"
        label2 = f"({(self.interval / 1000):.2f}s)"
        self.text1 = LABEL_FONT.render(label1, True, WHITE)
        self.text2 = LABEL_FONT.render(label2, True, WHITE)
        self.text1_rect = self.text1.get_rect(center=(block_rect.centerx - 15, block_rect.centery+block_font_offset-25))
        self.text2_rect = self.text2.get_rect(center=(block_rect.centerx, block_rect.centery+block_font_offset+20))

    def draw_text(self):
        self.image.blit(self.text1, self.text1_rect)
        self.image.blit(self.text2, self.text2_rect)
    
    def draw(self, surface):
        self.draw_base()
        self.draw_text()
        self.draw_lock(self.text1_rect)
        self.draw_ports(surface)

        surface.blit(self.image, self.rect)
    
    def update_logic(self):
        now = py.time.get_ticks()

        if now - self.last_toggle >= self.interval:
            self.powered = not self.powered
            self.last_toggle = now

        self.outputs[0].value = self.powered

    def on_click(self):
        self.index = (self.index+1) % len(self.intervals)
        self.update_text()

class LED(Block):
    LABEL = "LED"
    INPUTS = 1
    OUTPUTS = 0
    
    def __init__(self, pos, in_macro=False):
        super().__init__(pos, in_macro)
        self.colors = [RED, ORANGE, YELLOW, GREEN, BLUE, INDIGO, VIOLET]
        self.index = 0
        self.light = py.Surface((BLOCK_WIDTH // 8, BLOCK_HEIGHT))
        self.powered = False

    @property
    def color(self):
        return self.colors[self.index]
    
    def update_logic(self):
        self.powered = self.inputs[0].value

    def draw(self, surface):
        super().draw(surface)

        color = self.color if self.powered else DARK_GRAY
        self.light.fill(color)

        self.image.blit(self.light, self.light.get_rect(topright=self.image.get_rect().topright))
        surface.blit(self.image, self.rect)

        
    def on_click(self):
        self.index = (self.index + 1) % len(self.colors)