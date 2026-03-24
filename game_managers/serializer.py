import json

from setup.files import SAVE_DIR, AUTOSAVE_DIR
from setup.events import queue_message

from wiring import Wire

class FlattenContext:
    def __init__(self):
        self.next_id = 0
        self.block_map = {}
        self.macro_ports = {}
        self.blocks = []
        self.wires = []
        self.inputs = []
        self.outputs = []

    def add_block(self, block, original_id=None, top_level=False):
        block["id"] = self.next_id
        self.blocks.append(block)

        if top_level and original_id is not None:
            self.block_map[original_id] = self.next_id

        self.next_id += 1

        return block["id"]  
    
    def add_wire(self, src, dst):
        self.wires.append({
            "from": list(src),
            "to": list(dst),
        })
    
    def register_macro_input(self, macro_id, port_index, target):
        self.macro_ports[(macro_id, port_index, "in")] = target

    def register_macro_output(self, macro_id, port_index, target):
        self.macro_ports[(macro_id, port_index, "out")] = target
    
    def register_macro_ports(self, macro_block, macro_scene, local_map):
        for i, inp in enumerate(macro_scene.get("inputs", [])):
            self.register_macro_input(
                macro_block["id"], i,
                (local_map[inp["block"]], inp["port"])
            )

        for i, out in enumerate(macro_scene.get("outputs", [])):
            self.register_macro_output(
                macro_block["id"], i,
                (local_map[out["block"]], out["port"])
            )
            
    def resolve_port(self, block_id, port, direction):
        key = (block_id, port, direction)

        if key in self.macro_ports:
            return self.macro_ports[key]

        return (self.block_map[block_id], port)
    
    def map_local(self, local_map, old_id, new_id):
        local_map[old_id] = new_id

    def copy_wires(self, wires, id_map):
        for w in wires:
            src_id, src_port = w["from"]
            dst_id, dst_port = w["to"]

            self.add_wire(
                (id_map[src_id], src_port),
                (id_map[dst_id], dst_port)
            )

class SceneSerializer:
    def __init__(self, registry):
        self.registry = registry
        
    def serialize_blocks(self, blocks):
        block_ids = {b: i for i, b in enumerate(blocks)}

        data = []
        for b in blocks:
            data.append({
                "id": block_ids[b],
                "type": b.LABEL,
                "pos": [b.rect.centerx, b.rect.centery],
                "name": getattr(b, "name", b.LABEL),
                "state": b.get_state() if hasattr(b, "get_state") else None,

                "inputs": [p.value for p in b.inputs],
                "outputs": [p.value for p in b.outputs]
            })

        return data, block_ids

    def serialize_wires(self, wires, block_ids):
        data = []

        for w in wires:
            data.append({
                "from": [
                    block_ids[w.out.block],
                    w.out.block.outputs.index(w.out)
                ],
                "to": [
                    block_ids[w.inp.block],
                    w.inp.block.inputs.index(w.inp)
                ],
            })

        return data

    def serialize_io(self, scene):
        wires = scene["wires"]

        used_inputs = {tuple(w["to"]) for w in wires}
        used_outputs = {tuple(w["from"]) for w in wires}

        scene["inputs"] = [
            {"block": bi, "port": pi, "label": f"{b['type']} in {pi+1}"}
            for bi, b in enumerate(scene["blocks"])
            for pi in range(getattr(self.get_class(b), "INPUTS", 0))
            if (bi, pi) not in used_inputs
        ]

        scene["outputs"] = [
            {"block": bi, "port": po, "label": f"{b['type']} out {po+1}"}
            for bi, b in enumerate(scene["blocks"])
            for po in range(getattr(self.get_class(b), "OUTPUTS", 0))
            if (bi, po) not in used_outputs
        ]
    
    # Assign labels to unconnected ports and add to scene["inputs"] and scene["outputs"]

    def collect_macros(self, blocks):
        collected = {}

        def recurse(macro_cls):
            name = macro_cls.__name__
            if name in collected:
                return

            collected[name] = macro_cls.scene_data

            for block in macro_cls.scene_data["blocks"]:
                block_type = block["type"]
                cls = self.get_class(block)
                if cls and getattr(cls, "is_macro", False):
                    recurse(cls)

        for b in blocks:
            if hasattr(b.__class__, "is_macro"):
                recurse(b.__class__)

        return collected

    def validate_scene(self, scene):
        if not isinstance(scene, dict):
            return False

        blocks = scene["blocks"]
        wires = scene["wires"]

        if len(blocks) == 0:
            queue_message("Nothing to save.")
            return False
        
        if not isinstance(blocks, list) or not isinstance(wires, list):
            return False

        ids = set()
        for b in blocks:
            if "id" not in b or "type" not in b or "pos" not in b:
                return False

            if b["id"] in ids:
                return False
            ids.add(b["id"])

            if b["type"] not in self.registry:
                return False

        for w in wires:
            if "from" not in w or "to" not in w:
                return False

            src_id, _ = w["from"]
            dst_id, _ = w["to"]

            if src_id not in ids or dst_id not in ids:
                return False

        return True
    
    def serialize_scene(self, blocks, wires, include_macros=False):
        blocks_data, block_ids = self.serialize_blocks(blocks)
        wires_data = self.serialize_wires(wires, block_ids)

        scene = {
            "blocks": blocks_data,
            "wires": wires_data,
        }

        if include_macros:
            scene["macros"] = self.collect_macros(blocks)
            
        self.serialize_io(scene)

        # only flatten when exporting macros
        if not include_macros:
            scene = self.flatten_scene(scene)

        return scene

    # Flattening ---------- #
    def add_primitive_block(self, block, ctx, offset, top_level):
        new_block = block.copy()

        new_block["id"] = ctx.next_id
        new_block["pos"] = [
            block["pos"][0] + offset[0],
            block["pos"][1] + offset[1],
        ]

        ctx.blocks.append(new_block)

        if top_level:
            ctx.block_map[block["id"]] = ctx.next_id

        ctx.next_id += 1


    def expand_block(self, block, ctx, offset=(0,0), top_level=False):
        cls = self.get_class(block)

        if not getattr(cls, "is_macro", False):
            self.add_primitive_block(block, ctx, offset, top_level)
            return

        self.expand_macro(block, cls.scene_data, ctx, offset)

    def expand_macro(self, block, macro_scene, ctx, offset):
        macro_offset = (
            block["pos"][0] + offset[0],
            block["pos"][1] + offset[1],
        )

        local_map = {}

        for internal in macro_scene["blocks"]:
            before = ctx.next_id

            self.expand_block(internal.copy(), ctx, macro_offset)

            local_map[internal["id"]] = before

        ctx.copy_wires(macro_scene["wires"], local_map)
        ctx.register_macro_ports(block, macro_scene, local_map)

    def rebuild_wires(self, scene, ctx: FlattenContext):
        for wire in scene["wires"]:
            src_id, src_port = wire["from"]
            dst_id, dst_port = wire["to"]

            src = ctx.resolve_port(src_id, src_port, "out")
            dst = ctx.resolve_port(dst_id, dst_port, "in")      

            ctx.add_wire(src, dst)

    def rebuild_io(self, scene, ctx: FlattenContext):
        inputs = []
        outputs = []

        for inp in scene.get("inputs", []):
            block_id = inp["block"]
            port = inp["port"]

            target = ctx.resolve_port(block_id, port, "in")

            inputs.append({
                "block": target[0],
                "port": target[1],
                "label": inp.get("label")
            })

        for out in scene.get("outputs", []):
            block_id = out["block"]
            port = out["port"]

            source = ctx.resolve_port(block_id, port, "out")

            outputs.append({
                "block": source[0],
                "port": source[1],
                "label": out.get("label")
            })

        ctx.inputs = inputs
        ctx.outputs = outputs
        
    def flatten_scene(self, scene):
        ctx = FlattenContext()

        for block in scene["blocks"]:
            self.expand_block(block, ctx, top_level=True)

        self.rebuild_wires(scene, ctx)
        self.rebuild_io(scene, ctx)

        return {
            "blocks": ctx.blocks,
            "wires": ctx.wires,
            "inputs": ctx.inputs,
            "outputs": ctx.outputs
        }
    
    # --------------------- #

    def rebuild_scene(self, data, scene_obj, register_macro):
        scene_obj.clear()
        
        id_map = {}

        # register macros first
        for name, macro_scene in data.get("macros", {}).items():
            if name not in self.registry:
                register_macro(name, macro_scene)

        # rebuild blocks
        for b in data["blocks"]:
            cls = self.get_class(b)
            blk = cls(b["pos"])
            blk.name = b.get("name", blk.LABEL)

            blk.set_state(b.get("state"))

            for port, val in zip(blk.inputs, b.get("inputs", [])):
                port.value = val

            for port, val in zip(blk.outputs, b.get("outputs", [])):
                port.value = val

            scene_obj.add_block(blk)
            id_map[b["id"]] = blk

        # rebuild wires
        for w in data["wires"]:
            src = id_map[w["from"][0]]
            dst = id_map[w["to"][0]]

            wire = Wire(
                src.outputs[w["from"][1]],
                dst.inputs[w["to"][1]]
            )
            scene_obj.add_wire(wire)
        
    def save_to_file(self, name, blocks, wires, include_macros=True, autosave=False):
        scene = self.serialize_scene(blocks, wires, include_macros=include_macros)

        if not self.validate_scene(scene):
            return False

        if not name.endswith(".json"):
            name += ".json"

        if autosave:
            path = AUTOSAVE_DIR / name
        else:
            path = SAVE_DIR / name

        with open(path, "w") as f:
            json.dump(scene, f, indent=2) #import json at top

        return True
    
    def load_from_file(self, name, scene_obj, register_macro):
        if not name.endswith(".json"):
            name += ".json"

        path = SAVE_DIR / name
        if not path.exists():
            return False

        with open(path, "r") as f:
            data = json.load(f)

        self.rebuild_scene(data, scene_obj, register_macro)
        return True

    def is_valid_save_name(self, name):
        if not name:
            queue_message("Name cannot be empty")
            return False

        if "/" in name or "\\" in name:
            queue_message("Name cannot include '/' or '\\'")
            return False
        
        return True

    def get_class(self, block):
        if block["type"] in self.registry:
            return self.registry[block["type"]]
        
        else:
            raise KeyError("Block not in registry!")
        
