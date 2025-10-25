class AudioManager:
    def __init__(self):
        self.sounds = {}
        self.music = None

    def load_sound(self, name, file_path):
        self.sounds[name] = pygame.mixer.Sound(file_path)

    def play_sound(self, name):
        if name in self.sounds:
            self.sounds[name].play()

    def load_music(self, file_path):
        self.music = file_path
        pygame.mixer.music.load(file_path)

    def play_music(self, loop=-1):
        if self.music:
            pygame.mixer.music.play(loop)

    def stop_music(self):
        pygame.mixer.music.stop()

    def set_volume(self, volume):
        pygame.mixer.music.set_volume(volume)
        for sound in self.sounds.values():
            sound.set_volume(volume)