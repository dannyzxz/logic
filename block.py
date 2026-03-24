import pygame as py

import itertools
from wiring import Port

from setup.colors import GREEN, RED, BLACK, WHITE
from setup.fonts import LABEL_FONT, block_font_offset
from setup.widgets import BLOCK_WIDTH, BLOCK_HEIGHT

block_id_counter = itertools.count()

class Block(py.sprite.Sprite):
    LABEL = "Block"
    INPUTS = 2
    OUTPUTS = 1
    FUNC = None
    
    def __init__(self, pos, in_macro = False):
        super().__init__()
        if hasattr(self.__class__, "IMAGE_PATH") and self.IMAGE_PATH.exists():
            self.base_image = py.image.load(self.IMAGE_PATH).convert_alpha()
        
        else:
            self.base_image = py.Surface((BLOCK_WIDTH, BLOCK_HEIGHT), py.SRCALPHA)
            self.base_image.fill(BLACK)

        self.image = py.Surface(self.base_image.get_size(), py.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)
        self.mask = py.mask.from_surface(self.base_image)

        self.text = LABEL_FONT.render(self.LABEL, True, WHITE)

        self.lock_image = py.Surface((15, 15))

        self.id = next(block_id_counter)
        self.in_macro = in_macro

        self.movable = True
        self.moving = False
        self.move_offset = py.Vector2()

        self.is_macro = False
        self.inputs = [
            Port(self, (0, int(self.rect.height * (i + 1) / (self.INPUTS + 1))))
            for i in range(self.INPUTS)
        ]
        
        self.outputs = [
            Port(self, (self.rect.width+10, int(self.rect.height * (i + 1) / (self.OUTPUTS + 1))), True)
            for i in range(self.OUTPUTS)
        ]

        self.ports = self.inputs + self.outputs
 
    def start_movement(self, pos):
        self.moving = True
        self.move_offset = py.Vector2(self.rect.center) - py.Vector2(pos)

    def delete(self, blocks, wires):
        blocks.remove(self)

        for port in self.ports:
            for wire in port.connections[:]:
                wire.delete(wires)

    def draw_text(self, block_rect):
        text_rect = self.text.get_rect(
            center=(block_rect.centerx - 15, block_rect.centery+block_font_offset)
        )
        self.image.blit(self.text, text_rect)
        
        return text_rect

    def draw_lock(self, text_rect):
        lock_color = GREEN if self.movable else RED
        self.lock_image.fill(lock_color)

        self.image.blit(
            self.lock_image,
            self.lock_image.get_rect(bottomright=(text_rect.right + 20, text_rect.centery))
        )

    def draw_base(self):
        self.image.blit(self.base_image, (0, 0))

    def draw_ports(self, surface):
        for port in self.ports:
            port.draw(surface)

    def draw(self, surface):
        block_rect = self.image.get_rect()

        self.draw_base()
        text_rect = self.draw_text(block_rect)
        self.draw_lock(text_rect)
        self.draw_ports(surface)

        surface.blit(self.image, self.rect)

    def check_garbage(self, x, blocks, wires):
        if self.in_macro:
            return
        
        if self.rect.centerx < x and not self.moving:
            self.delete(blocks, wires)
        
        return
    
    def update_logic(self):
        if self.FUNC:
            values = [p.value for p in self.inputs]
            self.outputs[0].value = self.FUNC(*values)

    def update(self, x, blocks, wires):
        self.update_logic()
        self.check_garbage(x, blocks, wires)

    def copy(self):
        new = self.__class__(self.rect.center, in_macro=self.in_macro)

        new.movable = self.movable

        # copy port values
        for i, port in enumerate(self.inputs):
            new.inputs[i].value = port.value

        for i, port in enumerate(self.outputs):
            new.outputs[i].value = port.value

        return new
    
    def is_clicked(self, pos):
        local_x = pos[0] - self.rect.x
        local_y = pos[1] - self.rect.y

        if 0 <= local_x < self.rect.w and 0 <= local_y < self.rect.h:
            return self.mask.get_at((local_x, local_y))
        return False

    def on_click(self):
        pass

    def get_state(self):
        return None 
    # for blocks like switches, clock, etc 
    # with actual states independent of other blocks

    def set_state(self, state):
        pass