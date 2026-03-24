import pygame as py

from setup.colors import GREEN, RED
from setup.widgets import PORT_RADIUS, WIRE_WIDTH

class Port:
    def __init__(self, block, offset, is_output=False):
        self.block = block
        self.offset = py.Vector2(offset)
        self.is_output = is_output
        self.value = False
        self.connections = []

    @property
    def pos(self):
        return py.Vector2(self.block.rect.topleft) + self.offset

    def draw(self, surface):
        color = GREEN if self.value else RED
        py.draw.circle(surface, color, self.pos, PORT_RADIUS)

    def hit_test(self, mouse_pos):
        return self.pos.distance_to(py.Vector2(mouse_pos)) <= PORT_RADIUS

    def update(self):
        if self.is_output:
            return
        
        if not self.connections:
            self.value = False

        else:
            self.value = any(wire.out.value for wire in self.connections)

class Wire:
    def __init__(self, out_port: Port, in_port: Port):
        self.out = out_port
        self.inp = in_port
        out_port.connections.append(self)
        in_port.connections.append(self)

    def delete(self, wires):
        wires.remove(self)
        self.out.connections.remove(self)
        self.inp.connections.remove(self)

    def draw(self, surface):
        py.draw.line(
            surface,
            GREEN if self.out.value else RED,
            self.out.pos,
            self.inp.pos,
            WIRE_WIDTH
        )

    def hit_test(self, mouse_pos, threshold=6):
        p = py.Vector2(mouse_pos)
        a = self.out.pos
        b = self.inp.pos

        ab = b - a
        ap = p - a

        if ab.length_squared() == 0:
            return False

        t = max(0, min(1, ap.dot(ab) / ab.length_squared()))
        closest = a + ab * t

        return closest.distance_to(p) <= threshold
    
