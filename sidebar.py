import pygame as py

from setup.fonts import SIDEBAR_FONT
from setup.colors import MED_GRAY, DARK_GRAY, LIGHT_GRAY
from setup.widgets import SCREEN_HEIGHT

class Sidebar:
    def __init__(self, registry):
        self.rect = py.Rect(0, 0, 150, SCREEN_HEIGHT)
        self.scroll_offset = 0
        self.scroll_speed = 30
        self.items = []
        self.registry = registry
        self.visible = True

        self.resizing = False
        self.resize_margin = 8  # pixels from edge to grab
        self.min_width = 120
        self.max_width = 400
        self.resize_rect = py.Rect(self.rect.width, 0, 8, SCREEN_HEIGHT)

        self.refresh()

    @property
    def reflow_pos(self):
        return 10 - self.scroll_offset
    
    @property
    def block_width(self):
        return self.rect.width - 20
    
    def refresh(self):
        self.items.clear()

        for name, cls in self.registry.items():
            item = SidebarItem(
                self.block_width,
                name,
                cls
            )

            self.items.append(item)

        self.reflow(self.reflow_pos)

    def scroll(self, direction):
        self.scroll_offset += direction * self.scroll_speed
        self.scroll_offset = max(self.scroll_offset, 0)

        max_scroll = max(0, len(self.items) * 60 - self.rect.height)
        self.scroll_offset = min(self.scroll_offset, max_scroll)
        self.reflow(self.reflow_pos)

    def draw(self, surface):
        if not self.visible:
            return

        py.draw.rect(surface, DARK_GRAY, self.rect)
        py.draw.rect(surface, LIGHT_GRAY, self.resize_rect)

        for item in self.items:
            item.draw(surface)

        # resize handle
        
    def reflow(self, y):
        for item in self.items:
            item.rect.topleft = (10, y)
            y += 60

    def check_resize(self, mouse_pos):
        if self.resize_rect.collidepoint(mouse_pos):
            self.resizing = True

    def stop_resize(self):
        self.resizing = False

    def resize(self, mouse_x):
        if not self.resizing:
            return

        new_width = mouse_x - self.rect.left
        new_width = max(self.min_width, min(self.max_width, new_width))

        self.rect.width = new_width
        self.resize_rect.left = self.rect.right
        self.refresh()

class SidebarItem:
    def __init__(self, x, name, block_cls):
        self.rect = py.Rect(0, 0, x, 50)
        self.name = name
        self.label = SIDEBAR_FONT.render(self.name, True, (255, 255, 255))
        self.block_cls = block_cls
        self.dragging = False
        self.deletable = getattr(block_cls, "is_macro", False)

    def draw(self, surface):
        py.draw.rect(surface, MED_GRAY, self.rect)
        surface.blit(self.label, self.label.get_rect(center=self.rect.center))

    def hit_test(self, pos):
        return self.rect.collidepoint(pos)
