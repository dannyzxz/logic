from ublocks import Switch, Button, Power, Clock, LED
from block import Block

from setup.files import ASSET_DIR

def make_gate_class(name, inputs, func):
    image_path = ASSET_DIR / "images" / "gates" / f"{name.lower()}.png"

    class Gate(Block):
        TYPE = name
        LABEL = name
        INPUTS = inputs
        FUNC = staticmethod(func)
        IMAGE_PATH = image_path

    return Gate

gate_defs = {
    "NOT": {"inputs": 1, "func": lambda a: not a},
    "AND": {"inputs": 2, "func": lambda a, b: a and b},
    "OR": {"inputs": 2, "func": lambda a, b: a or b},
    "NAND": {"inputs": 2, "func": lambda a, b: not(a and b)},
    "NOR": {"inputs": 2, "func": lambda a, b: not(a or b)},
    "XOR": {"inputs": 2, "func": lambda a, b: a^b},
    "XNOR": {"inputs": 2, "func": lambda a, b: a==b},
    "Buffer": {"inputs": 1, "func": lambda a: a},
}

block_registry = {
    name: make_gate_class(name, **data)
    for name, data in gate_defs.items()
}

block_registry["Switch"] = Switch
block_registry["Button"] = Button
block_registry["Power"] = Power
block_registry["Clock"] = Clock
block_registry["LED"] = LED