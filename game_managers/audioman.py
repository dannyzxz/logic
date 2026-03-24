import pygame as py
import random as rd

from setup.files import ASSET_DIR
from setup.misc import MUSIC_FADE_IN
from setup.events import MUSIC_END_EVENT

class AudioManager:
    def __init__(self, settings):
        self.settings = settings

        self.has_started = True

        py.mixer.set_num_channels(16)

        # -----------------
        # MUSIC
        # -----------------
        self.music_folder = ASSET_DIR / "audio" / "music"
        self.sfx_folder = ASSET_DIR / "audio" / "sfx"
        self.supported = (".mp3", ".wav", ".ogg")

        self.music_queue = []
        self.current_track = None

    

        self.load_music_folder()
        self.load_sfx()

    def load_music_folder(self):
        if not self.music_folder.exists():
            return

        self.music_tracks = [
            path for path in self.music_folder.iterdir()
            if path.suffix.lower() in self.supported
        ]

        self.shuffle_music()

    def shuffle_music(self):
        self.music_queue = self.music_tracks.copy()
        rd.shuffle(self.music_queue)

    def play_next_track(self):
        if not self.settings.music_enabled:
            return
        
        if not self.music_queue:
            self.music_queue = self.music_tracks[:]
            rd.shuffle(self.music_queue)

        track = self.music_queue.pop(0)
        full_path = self.music_folder / track
        self.current_track = track
        py.mixer.music.load(full_path)
        py.mixer.music.play(fade_ms=MUSIC_FADE_IN) 

    def start_music(self):
        if self.settings.music_enabled and not self.settings.music_paused and not py.mixer.music.get_busy():
            self.play_next_track()

    def toggle_music(self):
        if not self.settings.music_enabled:
            self.settings.music_enabled = True

            if self.settings.music_paused and py.mixer.music.get_pos() != -1:
                py.mixer.music.unpause()

            else:
                self.play_next_track()

            self.settings.music_paused = False

        else:
            self.settings.music_enabled = False
            py.mixer.music.pause()
            self.settings.music_paused = True

    def toggle_sfx(self):
        self.settings.sfx_enabled = not self.settings.sfx_enabled

        for sound in self.sounds.values():
            sound.set_volume(self.settings.sfx_volume if self.settings.sfx_enabled else 0)

        

    def set_music_volume(self, volume):
        self.settings.music_volume = volume
        py.mixer.music.set_volume(volume)

    def load_sfx(self):
        self.sounds = {}

        if not self.sfx_folder.exists():
            return

        for file in self.sfx_folder.iterdir():
            if file.suffix.lower() in self.supported:
                sound = py.mixer.Sound(file)
                sound.set_volume(self.settings.sfx_volume)
                self.sounds[file.stem] = sound

    def play_sound(self, name):
        if not self.settings.sfx_enabled:
            return
        
        if name in self.sounds:
            py.mixer.find_channel(True).play(self.sounds[name])

    def set_sfx_volume(self, volume):
        self.settings.sfx_volume = volume
        for sound in self.sounds.values():
            sound.set_volume(volume)
    
    def handle_event(self, event):
        if event.type == MUSIC_END_EVENT and self.settings.music_enabled:
            self.play_next_track()