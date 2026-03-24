import pygame as py
import os
import pygame_widgets
from datetime import datetime

from setup.files import MACRO_DIR, SAVE_DIR, USER_DIR, AUTOSAVE_DIR
from setup.events import set_state, queue_message, set_pending_port, set_active_block

from registry import block_registry
from sidebar import Sidebar

from game_managers.scene import Scene
from game_managers.controller import Controller
from game_managers.macman import MacroManager
from game_managers.uiman import UIManager
from game_managers.serializer import SceneSerializer
from game_managers.audioman import AudioManager
from game_managers.settingsman import Settings

class Game:
    def __init__(self):
        self.clock = py.time.Clock()
        self.sidebar = Sidebar(block_registry)


        self.running = True
        self.state = "game"
        
        self.scene = Scene()

        self.pending_port = None
        self.active_block = None

        self.registry = block_registry

        self.settings = Settings()

        self.serializer = SceneSerializer(self.registry)
        self.audio = AudioManager(self.settings)

        self.mm = MacroManager(
            self.registry, 
            self.sidebar, 
            self.scene, 
            self.serializer.validate_scene)
        
        self.ui = UIManager( # most injections for button onClick
            scene=self.scene,
            audio=self.audio,
            settings=self.settings,
            serializer=self.serializer,
            register_macro=self.mm.register_macro,
            save_scene_to_macro=self.mm.save_scene_to_macro,
            sidebar = self.sidebar,
            # actions instead of game
            clear_scene=self.clear_scene,
            clear_data=self.clear_data,
            toggle_macro_naming=self.toggle_macro_naming,
            toggle_confirmations=self.toggle_confirmations,
            registry=self.registry,
            quit_game = lambda: setattr(self, "running", False),
            clear_interaction = self.reset_interaction_state
        )

        self.controller = Controller(
            self.sidebar, 
            self.scene.blocks, 
            self.scene.wires, 
            self.scene.add_block, 
            self.scene.add_wire, 
            self.mm.delete_macro
            )


        self.ui.create_overlays()
        self.ui.create_widgets()

        self.settings.load()
        self._apply_loaded_settings()

        if self.settings.music_enabled:
            self.audio.start_music()
    
    def _apply_loaded_settings(self):
        self.audio.set_music_volume(self.settings.music_volume)
        self.audio.set_sfx_volume(self.settings.sfx_volume)
        self.ui.volume_sliders[0].setValue(self.settings.music_volume)
        self.ui.volume_sliders[1].setValue(self.settings.sfx_volume)
        self.ui.refresh_audio_ui()
        if self.settings.music_enabled:
            self.audio.start_music()

        self.ui.pause_buttons[2].setText(
            f" Confirmations: \n           {'on' if self.settings.confirmations_enabled else 'off'}"
        )

        self.ui.pause_buttons[5].setText(
            f" Macro naming: \n           {'on' if self.settings.macro_naming_enabled else 'off'}"
        )

    def clear_scene(self):
        self.scene.clear()    

        set_pending_port(None)
        set_active_block(None)
        
        queue_message("Scene cleared.")

    def clear_data(self):
        save_files = list(SAVE_DIR.glob("*.json"))
        autosave_files = list(AUTOSAVE_DIR.glob("*.json"))
        macro_files = list(MACRO_DIR.glob("*.json"))
        settings = USER_DIR / "settings.json"

        if not (save_files or autosave_files or macro_files or settings.exists()):
            queue_message("No data to clear.")
            return

        # Delete save files
        for path in save_files:
            os.remove(path)

        # Delete macro files
        for path in macro_files:
            os.remove(path)

        for path in autosave_files:
            os.remove(path)

        # Delete settings
        if settings.exists():
            os.remove(settings)

        # Remove macro instances from scene
        for block in list(self.scene.blocks):
            if getattr(block.__class__, "is_macro", False):
                block.delete(self.scene.blocks, self.scene.wires)

        # Remove macro classes from registry
        macro_names = [
            name for name, cls in self.registry.items()
            if getattr(cls, "is_macro", False)
        ]

        for name in macro_names:
            self.mm.delete_macro(name)

        # Reset ui
        self.ui.sidebar.refresh()
        self.mm.macro_count = 1

        queue_message("Saved data cleared.")
    
    def update_game(self):
        self.scene.simulate()

        # Garbage collect blocks that drifted off screen
        for block in self.scene.blocks[:]:
            block.check_garbage(self.ui.sidebar.rect.width, self.scene.blocks, self.scene.wires)

        if self.ui.sidebar.resizing:
            self.ui.sidebar.resize(py.mouse.get_pos()[0])

    def update_sliders(self, events):
        pygame_widgets.update(events)

        music_vol = self.ui.volume_sliders[0].getValue()
        sfx_vol = self.ui.volume_sliders[1].getValue()

        self.audio.set_music_volume(music_vol)
        self.audio.set_sfx_volume(sfx_vol)

        self.ui.volume_labels[0].setText(f"Music Volume: {int(music_vol*100)}%")
        self.ui.volume_labels[1].setText(f"SFX Volume: {int(sfx_vol*100)}%")

    # Macro/save
    
    def confirm_macro_save(self, name):
        if not name:
            return

        self.mm.save_scene_to_macro(self.pending_macro_scene, custom_name=name)
        set_state("game")

    def confirm_scene_save(self, name):
        if not name:
            return

        self.serializer.save_to_file(name, self.scene.blocks, self.scene.wires, include_macros=True)
        set_state("game")
    
    def handle_macro_name_return(self):
        name = self.ui.textbox.getText().strip()

        if self.mm.is_valid_macro_name(name):
            scene = self.serializer.serialize_scene(self.scene.blocks, self.scene.wires, include_macros=False)
            self.mm.save_scene_to_macro(scene, custom_name=name)

            self.ui.textbox.setText("")
            queue_message(f"Macro saved: {name}")

            set_state("game")

    def handle_save_name_return(self):
        name = self.ui.textbox.getText().strip()
        
        if self.serializer.is_valid_save_name(name):
            self.serializer.save_to_file(name, self.scene.blocks, self.scene.wires, include_macros=True)

            self.ui.textbox.setText("")
            queue_message(f"Saved: {name}")

            set_state("game")   
    
    def handle_autosave(self):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        name = f"{timestamp}.json"
        self.ui.messages_muted = True
        
        if not self.serializer.save_to_file(name, self.scene.blocks, self.scene.wires, include_macros=True, autosave=True):
            self.ui.messages_muted = False
            return
        
        self.ui.messages_muted = False
        queue_message(f"Autosave")
    

    def quit(self):
        self.running = False
        
    def reset_interaction_state(self):
        set_pending_port(None)
        set_active_block(None)

    def toggle_macro_naming(self):
        self.settings.macro_naming_enabled = not self.settings.macro_naming_enabled

        self.ui.pause_buttons[5].setText(
            f" Macro naming: \n           {'on' if self.settings.macro_naming_enabled else 'off'}"
        )

    def toggle_confirmations(self):
        self.settings.confirmations_enabled = not self.settings.confirmations_enabled

        self.ui.pause_buttons[2].setText(
            f" Confirmations: \n           {'on' if self.settings.confirmations_enabled else 'off'}"
        )

  