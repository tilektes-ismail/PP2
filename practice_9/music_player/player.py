import pygame
import os

class MusicPlayer:
    def __init__(self, music_folder):
        pygame.mixer.init()

        self.music_folder = music_folder
        self.playlist = self.load_music()
        self.current_index = 0
        self.is_playing = False

    def load_music(self):
        files = [f for f in os.listdir(self.music_folder) if f.endswith(('.mp3', '.wav'))]
        return files

    def play(self):
        if not self.playlist:
            print("No music found.")
            return

        track = self.playlist[self.current_index]
        path = os.path.join(self.music_folder, track)

        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        self.is_playing = True

        print(f"Playing: {track}")

    def stop(self):
        pygame.mixer.music.stop()
        self.is_playing = False
        print("Stopped")

    def next_track(self):
        self.current_index = (self.current_index + 1) % len(self.playlist)
        self.play()

    def prev_track(self):
        self.current_index = (self.current_index - 1) % len(self.playlist)
        self.play()

    def get_current_track(self):
        if not self.playlist:
            return "No track"
        return self.playlist[self.current_index]