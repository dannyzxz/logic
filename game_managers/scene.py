from wiring import Wire

def simulate_until_stable(blocks, wires, max_iterations=20):
    for _ in range(max_iterations):
        prev = {id(blk): [p.value for p in blk.outputs] for blk in blocks}

        for block in blocks:
            block.update_logic()

        if all(
            [p.value for p in blk.outputs] == prev[id(blk)]
            for blk in blocks
        ):
            break

    for block in blocks:
        for port in block.inputs:
            port.update()

class Scene:
    def __init__(self):
        self.blocks = []
        self.wires = []

    def add_block(self, block):
        self.blocks.append(block)

    def remove_block(self, block):
        block.delete(self.blocks, self.wires)

    def add_wire(self, out_port, in_port):
        wire = Wire(out_port, in_port)
        self.wires.append(wire)
        return wire

    def remove_wire(self, wire):
        wire.delete(self.wires)

    def clear(self):
        self.blocks.clear()
        self.wires.clear()
        
    def simulate(self):
        simulate_until_stable(self.blocks, self.wires)

    def draw(self, surface):
        for wire in self.wires:
            wire.draw(surface)
            
        for block in self.blocks:
            block.draw(surface)