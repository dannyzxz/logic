import json

from setup.files import USER_DIR
from setup.events import queue_message

DEFAULTS = {
    "macro_naming_enabled": True,
    "confirmations_enabled": True,
    "music_enabled": True,
    "sfx_enabled": True,
    "music_volume": 0.5,
    "sfx_volume": 0.7,
    "music_paused": False
}

class Settings:
    def __init__(self):
        for key, val in DEFAULTS.items():
            setattr(self, key, val)
        
    def toggle(self, attr: str):
        if hasattr(self, attr) and isinstance(getattr(self, attr), bool):
            setattr(self, attr, not getattr(self, attr))

    def save(self):
        data = {k: getattr(self, k) for k in DEFAULTS}
        path = USER_DIR / "settings.json"
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        queue_message("Settings saved: will load on next startup")

    def load(self):
        path = USER_DIR / "settings.json"
        if not path.exists():
            return
        with open(path, "r") as f:
            data = json.load(f)
        for key, default in DEFAULTS.items():
            setattr(self, key, data.get(key, default))