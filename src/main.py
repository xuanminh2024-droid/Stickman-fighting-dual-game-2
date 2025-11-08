import pygame
from game import Game
try:
    from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
except Exception:
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS = 800, 600, 60

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Street Duel")
    clock = pygame.time.Clock()
    game = Game(screen)

    running = True
    while running:
        dt = clock.tick(FPS)  # ms since last frame
        events = pygame.event.get()
        for ev in events:
            if ev.type == pygame.QUIT:
                running = False

        game.update(dt, events)
        game.draw()
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()