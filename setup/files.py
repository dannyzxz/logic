from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

ASSET_DIR = BASE_DIR / "assets"
USER_DIR = BASE_DIR / "user"

FONT_DIR = ASSET_DIR / "fonts"

MACRO_DIR = USER_DIR / "macros"

SAVE_DIR = USER_DIR / "saves"
AUTOSAVE_DIR = SAVE_DIR / "autosaves"

os.makedirs(USER_DIR, exist_ok=True)
os.makedirs(MACRO_DIR, exist_ok=True)
os.makedirs(SAVE_DIR, exist_ok=True)
os.makedirs(AUTOSAVE_DIR, exist_ok=True)