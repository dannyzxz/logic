from PIL import Image
import pygame as py

class GifPlayer:
    def __init__(self, path):
        self.frames, self.durations = self.load_gif_frames(path)
        self.index = 0
        self.last_update = py.time.get_ticks()
  
    def load_gif_frames(self, path):
        frames = []
        durations = []

        gif = Image.open(path)

        try:
            while True:
                frame = gif.convert("RGBA")

                mode = frame.mode
                size = frame.size
                data = frame.tobytes()

                surface = py.image.frombytes(data, size, mode)
                frames.append(surface)

                durations.append(gif.info.get("duration", 100))  # ms

                gif.seek(gif.tell() + 1)
                
        except EOFError:
            pass

        return frames, durations

    def update(self):
        now = py.time.get_ticks()
        if now - self.last_update > self.durations[self.index]:
            self.index = (self.index + 1) % len(self.frames)
            self.last_update = now

    def draw(self, surface, pos):
        surface.blit(self.frames[self.index], pos)