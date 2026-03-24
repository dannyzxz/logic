import json
import os

from setup.files import MACRO_DIR
from setup.events import queue_message

from macro_cls import Macro

class MacroManager:
    def __init__(self, registry, sidebar, scene, validate_scene):
        self.registry = registry
        self.sidebar = sidebar
        self.scene = scene
        self.validate_scene = validate_scene

        self.macro_count = 1

    # Validation

    def normalize_scene(self, scene):
        return {
            "blocks": sorted(scene["blocks"], key=lambda b: (b["type"], tuple(b["pos"]))),
            "wires": sorted(scene["wires"], key=lambda w: (tuple(w["from"]), tuple(w["to"]))),
            "inputs": sorted(scene.get("inputs", []), key=lambda i: (i["block"], i["port"])),
            "outputs": sorted(scene.get("outputs", []), key=lambda o: (o["block"], o["port"])),
        }

    def check_dupe_macro(self, scene):
        normalized = self.normalize_scene(scene)

        for path in MACRO_DIR.glob("*.json"):
            with open(path, "r") as f:
                existing_scene = json.load(f)

            if self.normalize_scene(existing_scene) == normalized:
                return True

        return False

    def is_valid_macro_name(self, name):
        if not name:
            return False

        if name in self.registry:
            return False

        if len(name) > 20:
            return False
        
        if "/" in name or "\\" in name:
            queue_message("Name cannot include '/' or '\\'")
            return False
        
        return True

    def make_macro_class(self, name, scene):
        return type(
            name,
            (Macro,),
            {
                "LABEL": name,
                "INPUTS": len(scene["inputs"]),
                "OUTPUTS": len(scene["outputs"]),
                "scene_data": scene,
                "input_labels": [i.get("label", f"In {n}") for n, i in enumerate(scene["inputs"])],
                "output_labels": [o.get("label", f"Out {n}") for n, o in enumerate(scene["outputs"])],
                "is_macro": True
            }
        )
    # make macro using scene dict and assign to registry

    def save_macro_to_json(self, scene, name):
        path = MACRO_DIR / f"{name}.json"
        with open(path, "w") as f:
            json.dump(scene, f, indent=2)
        queue_message(f"Saved macro: {path}") 
    # Save scene dict as json

    def load_macros_from_json(self):
        for path in MACRO_DIR.glob("*.json"):
            name = path.stem  

            if not self.is_valid_macro_name(name):
                continue

            with open(path, "r") as f:
                scene = json.load(f)

            self.register_macro(name, scene)
    # Load and register 

    def register_macro(self, name, scene):
        MacroClass = self.make_macro_class(name, scene)
        self.registry[name] = MacroClass
        self.sidebar.refresh()
        queue_message(f"Registered macro: {name}")
    # Add to registry and sidebar

    def delete_macro(self, name):
        path = MACRO_DIR / f"{name}.json"
        if path.exists():
            os.remove(path)

        for block in list(self.scene.blocks):
            if block.__class__.__name__ == name:
                self.scene.remove_block(block)

        if name in self.registry:
            del self.registry[name]

        self.sidebar.refresh()

        queue_message(f"Macro '{name}' deleted.")
    # Delete macro file, remove instances from scene, unregister, refresh sidebar

    def save_scene_to_macro(self, scene, custom_name = None):
        name = custom_name if custom_name else f"Macro {self.macro_count}"
        
        if self.check_dupe_macro(scene):
            queue_message("Macro already exists")
            return 

        if not self.validate_scene(scene):
            queue_message("Not valid macro")
            return 

        self.save_macro_to_json(scene, name)
        self.register_macro(name, scene)
        self.macro_count += 1
        queue_message(f"Macro '{name}' created.")
    # Uses above functions to handle macro creation
