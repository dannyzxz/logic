import pygame as py

from wiring import Wire

from setup.events import set_active_block, set_pending_port, play_sound

class Controller:
    def __init__(self, sidebar, blocks, wires, add_block, add_wire, delete_macro):
        self.blocks = blocks
        self.wires = wires
        self.add_block = add_block
        self.add_wire = add_wire
        self.delete_macro = delete_macro
        self.sidebar = sidebar

    def handle_block_creation(self, block, pos):
        self.add_block(block)
        block.start_movement(pos)
        set_active_block(block)

    def check_for_port_clicks(self, pos):
        for block in self.blocks:
            for port in block.ports:
                if port.hit_test(pos):
                    return port
        return None
    
    def check_for_block_clicks(self, e):
        for block in self.blocks: 
            if block.is_clicked(e.pos):
                mods = py.key.get_mods()

                if mods & py.KMOD_SHIFT:
                    new = block.copy()
                    self.handle_block_creation(new, py.mouse.get_pos())

                elif block.movable and not self.check_for_port_clicks(e.pos):
                    block.start_movement(e.pos)
                    set_active_block(block)
            
                break
    
    def check_for_sidebar_item_creation(self, e):
        for item in self.sidebar.items:
            if item.hit_test(e.pos) and self.sidebar.visible:
                play_sound("pop")

                new = item.block_cls(e.pos)
                self.handle_block_creation(new, e.pos)

    def check_right_clicks(self, pos):
        for block in self.blocks:
            if block.rect.collidepoint(pos):
                block.movable = not block.movable
                if not block.movable:
                    play_sound("lock")
            
        for item in self.sidebar.items:
            if item.deletable and item.hit_test(pos):
                self.delete_macro(item.name)
                return
    
    def check_click_hold(self):
        click = py.mouse.get_pressed()
        pos = py.mouse.get_pos()

        if click[0]: # left
            for block in self.blocks:
                if block.moving:
                    block.rect.center = py.Vector2(pos) + block.move_offset

        elif click[2]: # right
            for wire in self.wires: 
                if wire.hit_test(pos):
                    wire.delete(self.wires)
                    set_pending_port(None) 

    def connect_ports(self, pending_port, clicked_port):
        if pending_port.block is clicked_port.block: # wire ports on same block = invalid
            return
        
        if pending_port.is_output == clicked_port.is_output: # both input / output = invalid
            return
        
        play_sound("zap")

        out, inp = (pending_port, clicked_port) if pending_port.is_output else (clicked_port, pending_port)

        self.add_wire(out, inp) 
        
    def handle_port_connections(self, pending_port, pos):
        clicked_port = self.check_for_port_clicks(pos)

        if not clicked_port:
            set_pending_port(None)
            return

        if not pending_port:
            set_pending_port(clicked_port)
            return

        
        self.connect_ports(pending_port, clicked_port)
        set_pending_port(None)
