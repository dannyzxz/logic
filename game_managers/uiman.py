import pygame as py
import json
import pygame_widgets
from pygame_widgets.textbox import TextBox
from pygame_widgets.button import Button
from pygame_widgets.slider import Slider

from setup.files import ASSET_DIR, SAVE_DIR, MACRO_DIR
from setup.fonts import LABEL_FONT, TITLE_FONT, LABEL_FONT_SIZE, LABEL_HEIGHT, BUTTON_FONT_SIZE, SMALL_BUTTON_FONT_SIZE, PAUSE_TITLE
from setup.colors import BLACK
from setup.events import set_state, queue_message
from setup.widgets import (
    PAUSE_BUTTON_COLS, BUTTON_START_X, BUTTON_START_Y,
    BUTTON_WIDTH, BUTTON_HEIGHT, BUTTON_SPACING,
    TEXTBOX_WIDTH, TEXTBOX_HEIGHT,
    SLIDER_SPACING, SLIDER_WIDTH, SLIDER_HEIGHT,
    TEXT_LABEL_WIDTH, LABEL_SPACING,
    TEXT_LABEL_HEIGHT, MACRO_OVERLAY_WIDTH, MACRO_OVERLAY_HEIGHT, WIRE_WIDTH
)
from setup.misc import SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_CENTER

from game_managers.gifman import GifPlayer

from setup.colors import RED, BLUE, WHITE, TRANSPARENT_BLACK


class UIManager:
    def __init__(self, *, scene, audio, settings, serializer, register_macro, 
            save_scene_to_macro, sidebar, quit_game, clear_scene, clear_data, 
            toggle_macro_naming, toggle_confirmations, registry, clear_interaction):
        
        self.scene = scene
        self.audio = audio
        self.settings = settings
        self.serializer = serializer
        self.register_macro = register_macro
        self.save_scene_to_macro = save_scene_to_macro
        self.sidebar = sidebar
        
        self.quit_game = quit_game
        self.clear_scene = clear_scene
        self.clear_data = clear_data
        self.toggle_macro_naming = toggle_macro_naming
        self.toggle_confirmations = toggle_confirmations
        self.clear_interaction = clear_interaction
        self.registry = registry

        self.gifplayer = GifPlayer

        self.load_buttons = []
        self.macro_buttons = []
        
        self.pause_button_data = [
            ("Resume", lambda: set_state("game")),

            ("Exit", self.quit_game),

            ("Confirmations:\n          on", lambda: self.start_confirm_menu(
                "Turn off all confirmations?",
                self.toggle_confirmations
            )),

            ("Save", self.start_scene_save),

            ("Load scene", lambda: self.start_load_menu()),

            ("Macro naming:\n          on", self.toggle_macro_naming),

            ("Save Macro", self.start_macro_save),

            ("Load Macros", self.start_macro_load_menu),

            ("Toggle Sidebar", lambda: setattr(self.sidebar, "visible", not self.sidebar.visible)),

            ("Audio settings", lambda: self.start_audio_menu()),

            ("Save settings", self.settings.save),

            ("yo", lambda: queue_message("she logic on my gate till i compute")),

            
             ("Clear Scene", lambda: self.start_confirm_menu(
                "Clear scene?",
                self.clear_scene
            )),

            ("Clear Data", lambda: self.start_confirm_menu(
                "Clear all saved data?",
                self.clear_data
            )),

            ("Help", lambda: self.start_help_screen()),

        ]

        self.help_entries = [
            {
                "text": "Use the sidebar to add blocks.",
                "gif_path": ASSET_DIR / "gifs" / "sidebar_block.gif"
            },
            {
                "text": "Right-click blocks to lock/unlock.",
                "gif_path": ASSET_DIR / "gifs" / "lock.gif"
            },
            {
                "text": "Connect two ports with a wire by clicking on them.",
                "gif_path": ASSET_DIR / "gifs" / "connect.gif"
            },
            {
                "text": "Delete a wire by right clicking it.",
                "gif_path": ASSET_DIR / "gifs" / "delete_wire.gif"
            },
            {
                "text": "Drag blocks to sidebar to delete",
                "gif_path": ASSET_DIR / "gifs" / "delete_block.gif"
            },
            {
                "text": "Macros are collections of blocks represented by one block",
                "gif_path": ASSET_DIR / "gifs" / "macro.gif"
            },
            {
                "text": "You can use a macro in another macro",
                "gif_path": ASSET_DIR / "gifs" / "nested_macro.gif"
            },
            {
                "text": "Buffers act as inputs/outputs for macros",
                "gif_path": ASSET_DIR / "gifs" / "buffer.gif"
            },
        ]

        for entry in self.help_entries:
            entry["text_surf"] = LABEL_FONT.render(entry["text"], True, BLACK)

        self.message = None
        self.message_start = None
        self.message_duration = None
        self.messages_muted = False
        self.active_help_gif = None

    # button funcs
    def confirm_yes(self):
        if self.confirm_callback:
            self.confirm_callback()

        self.hide_widgets(self.pause_buttons)
        set_state("paused")

    def confirm_no(self):
        self.hide_widgets(self.pause_buttons)
        set_state("paused")
       
    # Create widgets and overlays
    def create_pause_buttons(self):
        self.pause_buttons = []

        for i, (text, func) in enumerate(self.pause_button_data):
            row = i // PAUSE_BUTTON_COLS
            col = i % PAUSE_BUTTON_COLS

            x = BUTTON_START_X + col * (BUTTON_WIDTH + BUTTON_SPACING)
            y = BUTTON_START_Y + row * (BUTTON_HEIGHT + BUTTON_SPACING)

            btn = Button(
                self.screen,
                x, y,
                BUTTON_WIDTH,
                BUTTON_HEIGHT,
                text=text,
                fontSize=BUTTON_FONT_SIZE,
                onClick=func
            )

            self.pause_buttons.append(btn)

        self.pause_buttons[12].textColour = RED
        self.pause_buttons[13].textColour = RED

    def create_confirm_buttons(self):
        self.confirm_buttons = []

        yes = Button(
            self.screen,
            self.confirm_overlay_rect.centerx - BUTTON_WIDTH - BUTTON_SPACING // 2,
            self.confirm_overlay_rect.top + self.confirm_overlay_rect.height // 2 - BUTTON_HEIGHT // 2,
            BUTTON_WIDTH,
            BUTTON_HEIGHT,
            text="Yes",
            fontSize=BUTTON_FONT_SIZE,
            onClick=self.confirm_yes
        )

        no = Button(
            self.screen,
            self.confirm_overlay_rect.centerx + BUTTON_SPACING // 2,
            self.confirm_overlay_rect.top + self.confirm_overlay_rect.height // 2 - BUTTON_HEIGHT // 2,
            BUTTON_WIDTH,
            BUTTON_HEIGHT,
            text="No",
            fontSize=BUTTON_FONT_SIZE,
            onClick=self.confirm_no
        )
        self.confirm_buttons.append(yes)
        self.confirm_buttons.append(no)

    def create_help_buttons(self):
        self.gif_buttons = []

        for entry in self.help_entries:

            def make_callback(path):
                def callback():
                    # Stop previous animation
                    if self.active_help_gif:
                        self.active_help_gif.playing = False
                        self.active_help_gif.index = 0

                    # Set new active gif
                    self.active_help_gif = self.gifplayer(path)
                    self.active_help_gif.index = 0
                    self.active_help_gif.last_update = py.time.get_ticks()
                    self.active_help_gif.playing = True
                return callback

            btn = Button(
                self.screen,
                0, 0,
                120,
                40,
                text="Play",
                fontSize=SMALL_BUTTON_FONT_SIZE,
                onClick=make_callback(entry["gif_path"]),
                radius = 60
            )

            self.gif_buttons.append(btn)
    
    def create_audio_widgets(self):
        self.audio_buttons = []
        self.volume_sliders = []
        self.volume_labels = []

        total_width = BUTTON_WIDTH * 2 + BUTTON_SPACING
        center_x = SCREEN_WIDTH // 2 - total_width // 2
        center_y = SCREEN_HEIGHT // 2 - BUTTON_HEIGHT

        total_slider_width = SLIDER_WIDTH * 2 + SLIDER_SPACING
        slider_x = SCREEN_WIDTH // 2 - total_slider_width // 2
        slider_y = int(SCREEN_HEIGHT * 2 / 3)

        toggle_music = Button(
            self.screen,
            center_x,

            center_y,
            BUTTON_WIDTH, BUTTON_HEIGHT,
            text=f" Music: \n    {'on' if self.settings.music_enabled else 'off'}",
            fontSize=BUTTON_FONT_SIZE,
            onClick=lambda: (self.audio.toggle_music(),
                             self.refresh_audio_ui())
        )

        toggle_sfx = Button(
            self.screen,
            center_x + BUTTON_WIDTH + BUTTON_SPACING,
            center_y,
            BUTTON_WIDTH, BUTTON_HEIGHT,
            text=f" SFX: \n  {'on' if self.settings.sfx_enabled else 'off'}",
            fontSize=BUTTON_FONT_SIZE,
            onClick=lambda:  (self.audio.toggle_sfx(),
                             self.refresh_audio_ui())
        )

        next = Button(
            self.screen,
            SCREEN_WIDTH // 2 - BUTTON_WIDTH // 2,
            center_y + BUTTON_HEIGHT + BUTTON_SPACING,
            BUTTON_WIDTH, BUTTON_HEIGHT,
            text="Next track",
            fontSize=BUTTON_FONT_SIZE,
            onClick=lambda: self.audio.play_next_track()
        )

        music_slider = Slider(
            self.screen,
            slider_x,
            slider_y,
            SLIDER_WIDTH,
            SLIDER_HEIGHT,
            min=0,
            max=1,
            step=0.01,
            handleColour=BLUE,
            vertical=True
        )

        sfx_slider = Slider(
            self.screen,
            slider_x + SLIDER_WIDTH + SLIDER_SPACING,
            slider_y,
            SLIDER_WIDTH,
            SLIDER_HEIGHT,
            min=0,
            max=1,
            step=0.01,
            handleColour=BLUE,
            vertical=True
        )

        music_label = TextBox(
            self.screen,
            slider_x - TEXT_LABEL_WIDTH - LABEL_SPACING,
            slider_y,
            TEXT_LABEL_WIDTH, TEXT_LABEL_HEIGHT,
            text=f"Music Volume: {int(self.settings.music_volume*100)}%",
            fontSize=LABEL_FONT_SIZE,
            borderThickness=0
        )

        sfx_label = TextBox(
            self.screen,
            slider_x + SLIDER_WIDTH *2 + SLIDER_SPACING + LABEL_SPACING,
            slider_y,
            TEXT_LABEL_WIDTH - 50, TEXT_LABEL_HEIGHT,
            text=f"SFX Volume: {int(self.settings.sfx_volume*100)}%",
            fontSize=LABEL_FONT_SIZE,
            borderThickness=0
        )

        music_label.disable()
        sfx_label.disable()
        
        self.audio_buttons.extend([toggle_music, toggle_sfx, next])
        self.volume_sliders.extend([music_slider, sfx_slider])
        self.volume_labels.extend([music_label, sfx_label])
    
    def create_widgets(self):
        self.create_pause_buttons()
        self.create_confirm_buttons()
        self.create_help_buttons()
        self.create_audio_widgets()

        self.textbox = TextBox(
            self.screen,
            self.naming_overlay_rect.left + (MACRO_OVERLAY_WIDTH - TEXTBOX_WIDTH) // 2,
            self.naming_overlay_rect.top + (MACRO_OVERLAY_HEIGHT - TEXTBOX_HEIGHT) // 2,
            TEXTBOX_WIDTH,
            TEXTBOX_HEIGHT,
            fontSize=BUTTON_FONT_SIZE,
            borderThickness=2,
            placeholderText="Enter name",
        )

        self.hide_widgets()
    
    def create_overlays(self):
        self.screen = py.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), py.RESIZABLE)

        self.transparent_overlay = py.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), py.SRCALPHA)
        self.transparent_overlay_rect = self.transparent_overlay.get_rect(center=SCREEN_CENTER)

        self.naming_overlay = py.Surface((SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), py.SRCALPHA)
        self.naming_overlay_rect = self.naming_overlay.get_rect(center=SCREEN_CENTER)

        self.message_overlay = py.Surface((SCREEN_WIDTH//2, SCREEN_HEIGHT//6), py.SRCALPHA)
        self.message_overlay_rect = self.message_overlay.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//6))

        self.confirm_overlay = py.Surface((SCREEN_WIDTH // 3, SCREEN_HEIGHT // 4), py.SRCALPHA)
        self.confirm_overlay_rect = self.confirm_overlay.get_rect(center=SCREEN_CENTER)

    def hide_widgets(self, exception: list = None):
        groups = [
            self.pause_buttons,
            self.load_buttons,
            self.macro_buttons,
            self.confirm_buttons,
            self.gif_buttons,
            self.audio_buttons,
            self.volume_sliders,
            self.volume_labels,
            [self.textbox]
        ]

        for group in groups:
            for widget in group:
                widget.hide()

        if exception:
            for widget in exception:
                widget.show()
    # Hides all widgets except exception, if given

    # Build func (build buttons which represent saved data - all macros/saves))
    def build_save_load_menu(self):
        self.load_buttons.clear()

        saves = list(SAVE_DIR.glob("*.json"))

        for i, path in enumerate(saves):
            name = path.stem

            btn = Button(
                self.screen,
                SCREEN_WIDTH // 2 - BUTTON_WIDTH // 2,
                BUTTON_START_Y + i * (BUTTON_HEIGHT + BUTTON_SPACING),
                BUTTON_WIDTH,
                BUTTON_HEIGHT,
                text=name,
                fontSize=BUTTON_FONT_SIZE,
                onClick=lambda n=name: self.load_scene_on_button_click(n)
            )

            self.load_buttons.append(btn)
         
    def build_macro_load_menu(self):
        self.macro_buttons.clear()

        macros = list(MACRO_DIR.glob("*.json"))

        for i, path in enumerate(macros):
            name = path.stem

            # Skip if already registered
            if name in self.registry:
                continue

            btn = Button(
                self.screen,
                SCREEN_WIDTH // 2 - BUTTON_WIDTH // 2,
                BUTTON_START_Y + i * (BUTTON_HEIGHT + BUTTON_SPACING),
                BUTTON_WIDTH,
                BUTTON_HEIGHT,
                text=name,
                fontSize=BUTTON_FONT_SIZE,
                onClick=lambda n=name, b=i: self.load_macro_on_button_click(n)
            )

            self.macro_buttons.append(btn)
    
    # Load appropiate data based on button clicked
    def load_scene_on_button_click(self, name):
        self.serializer.load_from_file(
            name,
            self.scene,
            self.register_macro
        )
        set_state("game")

    def load_macro_on_button_click(self, name) -> None:
        path = MACRO_DIR / f"{name}.json"

        if not path.exists():
            return

        with open(path, "r") as f:
            scene = json.load(f)

        self.register_macro(name, scene)

        self.build_macro_load_menu()

        if not self.macro_buttons:
            queue_message("No more macros to load")
            self.start_pause_menu()
            return

        for i, btn in enumerate(self.macro_buttons):
            btn.setY(BUTTON_START_Y + i * (BUTTON_HEIGHT + BUTTON_SPACING))

        self.hide_widgets(self.macro_buttons)
        
    # Draw
    def draw_game(self, pending_port):
        for wire in self.scene.wires:
            wire.draw(self.screen)
            
        for block in self.scene.blocks:
            block.draw(self.screen)
        
        if pending_port:
            py.draw.line(
                self.screen,
                BLACK,
                pending_port.pos,
                py.mouse.get_pos(),
                WIRE_WIDTH
            )

        self.sidebar.draw(self.screen)
        
    def draw_pause_screen(self, events):
        self.transparent_overlay.fill(TRANSPARENT_BLACK) 
        self.screen.blit(self.transparent_overlay, (0, 0))

        self.screen.blit(PAUSE_TITLE, PAUSE_TITLE.get_rect(
            center=(self.transparent_overlay_rect.centerx, self.transparent_overlay_rect.height//20)
            ))

        pygame_widgets.update(events)
    
    def draw_naming_screen(self, events):
        self.naming_overlay.fill(TRANSPARENT_BLACK)
        self.screen.blit(self.naming_overlay, self.naming_overlay_rect)

        pygame_widgets.update(events)

    def draw_confirmation_screen(self, events):
        self.confirm_overlay.fill(TRANSPARENT_BLACK)
        self.screen.blit(self.confirm_overlay, self.confirm_overlay_rect)

        text_rect = self.confirm_text.get_rect(
            center=(self.confirm_overlay_rect.centerx,
                    self.confirm_overlay_rect.top + 40)
        )
        self.screen.blit(self.confirm_text, text_rect)

        pygame_widgets.update(events)
    
    def draw_help_screen(self, events):
        self.screen.fill(WHITE)

        y = 100
        left_margin = 80
        spacing = 20

        for i, entry in enumerate(self.help_entries):
            text_surface = entry["text_surf"]
            button = self.gif_buttons[i]

            # Draw text first
            text_x = left_margin
            text_y = y
            self.screen.blit(text_surface, (text_x, text_y))

            # Position button to the right of text
            text_width = text_surface.get_width()

            button_x = text_x + text_width + spacing
            
            text_height = LABEL_HEIGHT
            button_height = button.getHeight()

            button_y = y + (text_height - button_height) // 2


            button.setX(button_x)
            button.setY(button_y)

            y += 80

        # Draw active gif on right side
        if self.active_help_gif:
            self.active_help_gif.update()

            gif_surface = self.active_help_gif.frames[0]
            gif_w = gif_surface.get_width()
            gif_h = gif_surface.get_height()

            right_x = self.screen.get_width() - gif_w - 100
            center_y = SCREEN_HEIGHT // 2 - gif_h // 2

            self.active_help_gif.draw(self.screen, (right_x, center_y))

        pygame_widgets.update(events)

    def draw_menu(self, pending_port, events): # load menus + audio menu
        self.draw_game(pending_port)
        
        self.transparent_overlay.fill(TRANSPARENT_BLACK) 
        self.screen.blit(self.transparent_overlay, (0, 0))

        pygame_widgets.update(events)

    def draw(self, state, pending_port, events):
        self.draw_game(pending_port)

        if state == "paused":
            self.draw_pause_screen(events)

        elif state == "macro_creation":
            self.draw_naming_screen(events)

        elif state == "saving_scene":
            self.draw_naming_screen(events)

        elif state == "confirmation":
            self.draw_confirmation_screen(events)

        elif state == "help":
            self.draw_help_screen(events)

        elif state == "save_load_menu":
            self.draw_menu(pending_port, events)

        elif state == "macro_load_menu":
            self.draw_menu(pending_port, events)

        elif state == "audio_menu":
            self.draw_menu(pending_port, events)
            
        self.draw_message()

    # Hide uneccecary widgets, set active block/pending port to none 
    def start_game(self):
        self.clear_interaction()

        self.hide_widgets()
        set_state("game")

    def start_pause_menu(self):
        self.clear_interaction()

        self.hide_widgets(self.pause_buttons)
        py.display.flip()
        set_state("paused")

    def start_naming_menu(self):
        self.clear_interaction()
        
        self.hide_widgets([self.textbox])
    
    def start_load_menu(self):
        self.clear_interaction()

        self.build_save_load_menu()
        if not self.load_buttons:
            queue_message("Nothing to load.")
            return
        
        self.hide_widgets(self.load_buttons)
        set_state("save_load_menu")

    def start_macro_load_menu(self):
        self.clear_interaction()

        self.build_macro_load_menu()

        if not self.macro_buttons:
            queue_message("No macros to load.")
            return

        self.hide_widgets(self.macro_buttons)
        set_state("macro_load_menu")

    def start_confirm_menu(self, message: str, on_confirm):
        self.clear_interaction()

        self.confirm_callback = on_confirm

        if not self.settings.confirmations_enabled:
            self.confirm_callback()
            set_state("paused")
            return

        self.confirm_text = TITLE_FONT.render(message, True, WHITE)

        self.hide_widgets(self.confirm_buttons)
        set_state("confirmation")
    
    def start_help_screen(self):
        self.clear_interaction()


        self.hide_widgets(self.gif_buttons)
        set_state("help")
    
    def start_audio_menu(self):
        self.clear_interaction()

        self.hide_widgets(self.audio_buttons + self.volume_sliders + self.volume_labels)
        set_state("audio_menu")

    def start_macro_save(self):
        scene = self.serializer.serialize_scene(self.scene.blocks, self.scene.wires, include_macros=False)

        if not self.serializer.validate_scene(scene):
            queue_message("Invalid macro")
            return

        self.pending_macro_scene = scene

        if self.settings.macro_naming_enabled:
            self.start_naming_menu()
            set_state("macro_creation")
        else:
            self.save_scene_to_macro(scene)

    def start_scene_save(self):
        scene = self.serializer.serialize_scene(self.scene.blocks, self.scene.wires, include_macros=True)

        if not self.serializer.validate_scene(scene):
            queue_message("Nothing to save.")
            return

        self.start_naming_menu()
        set_state("saving_scene")
    
    def refresh_audio_ui(self):
        self.audio_buttons[0].setText(
            f" Music: \n    {'on' if self.settings.music_enabled else 'off'}"
        )

        self.audio_buttons[1].setText(
            f" SFX: \n  {'on' if self.settings.sfx_enabled else 'off'}"
        )

        if self.settings.music_enabled:
            self.audio_buttons[2].enable()
        else:
            self.audio_buttons[2].disable()

    # Other ui
    def queue_message(self, message, duration=2500):
        if self.messages_muted:
            return
         
        self.message = TITLE_FONT.render(message, True, WHITE)
        self.message_start = py.time.get_ticks()
        self.message_duration = duration
    
    def draw_message(self):
        if not self.message:
            return

        elapsed = py.time.get_ticks() - self.message_start

        if elapsed > self.message_duration:
            self.message = None
            return

        progress = elapsed / self.message_duration

        alpha = 255 - int(255 * progress)

        # Movement amount
        y_offset = int(90 * (1 - (1 - progress) ** 2))

        # Move overlay rect upward
        moving_rect = self.message_overlay_rect.copy()
        moving_rect.centery -= y_offset

        # Apply alpha
        self.message_overlay.fill((0, 0, 0, min(180, alpha)))
        self.message.set_alpha(alpha)

        # Draw overlay at moved position
        self.screen.blit(self.message_overlay, moving_rect)

        # Draw text centered in moved overlay
        text_rect = self.message.get_rect(center=moving_rect.center)
        self.screen.blit(self.message, text_rect)

