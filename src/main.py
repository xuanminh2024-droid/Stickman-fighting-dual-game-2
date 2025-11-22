import sys
import pygame

# try to read optional settings; fall back to defaults
try:
    import settings
    SCREEN_WIDTH = getattr(settings, "SCREEN_WIDTH", 900)
    SCREEN_HEIGHT = getattr(settings, "SCREEN_HEIGHT", 520)
    FPS = getattr(settings, "FPS", 60)
except Exception:
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS = 900, 520, 60

# import the Game class from game.py
from game import Game

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Street Duel")
    clock = pygame.time.Clock()
    game = Game(screen)

    running = True
    while running: 
        dt = clock.tick(FPS)
        events = pygame.event.get()
        for ev in events:
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                running = False

        game.update(dt, events)
        game.draw()
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()