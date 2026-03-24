from game_managers.scene import Scene

from wiring import Wire
from block import Block

from registry import block_registry

from setup.fonts import IO_FONT
from setup.colors import WHITE
from setup.widgets import IO_LABEL_OFFSET

class Macro(Block):
    scene_data = None  # set by make_macro_class, renamed from 'scene' to avoid confusion

    def __init__(self, pos, in_macro=False):
        super().__init__(pos, in_macro=in_macro)
        self.build()

    def build(self):
        self.scene = Scene()
        block_list = []

        for b in self.scene_data["blocks"]:
            cls = block_registry[b["type"]]

            blk = cls((0, 0), in_macro=True)

            if b.get("state"):
                blk.set_state(b["state"])

            for i, val in enumerate(b.get("inputs", [])):
                blk.inputs[i].value = val

            for i, val in enumerate(b.get("outputs", [])):
                blk.outputs[i].value = val

            self.scene.add_block(blk)
            block_list.append(blk)

        for w in self.scene_data["wires"]:
            src = block_list[w["from"][0]]
            dst = block_list[w["to"][0]]
            self.scene.add_wire(src.outputs[w["from"][1]], dst.inputs[w["to"][1]])

        self._block_list = block_list
        self._built = True

    def update_logic(self):
        # Push macro inputs into the internal scene
        for i, item in enumerate(self.scene_data["inputs"]):
            blk = self._block_list[item["block"]]
            blk.inputs[item["port"]].value = self.inputs[i].value

        # Run the same eval as the top-level scene
        self.scene.simulate()

        # Pull internal outputs back out
        for i, item in enumerate(self.scene_data["outputs"]):
            blk = self._block_list[item["block"]]
            self.outputs[i].value = blk.outputs[item["port"]].value
    
    def draw(self, surface): # use super.draw 
        super().draw(surface)

        for i, port in enumerate(self.inputs):
            label = self.input_labels[i]
            text = IO_FONT.render(label, True, WHITE)
            text_rect = text.get_rect()
            text_rect.midright = (
                port.pos[0] - IO_LABEL_OFFSET,
                port.pos[1]
            )
            surface.blit(text, text_rect)

        for i, port in enumerate(self.outputs):
            label = self.output_labels[i]
            text = IO_FONT.render(label, True, WHITE)
            text_rect = text.get_rect()
            text_rect.midleft = (
                port.pos[0] + IO_LABEL_OFFSET,
                port.pos[1]
            )
            surface.blit(text, text_rect)

    def save_state(self):
        state = {}

        for block in self.internal_blocks:
            block_state = {}

            for port in block.ports:
                block_state[port.name] = port.value

            state[block.id] = block_state

        self.saved_state = state

   