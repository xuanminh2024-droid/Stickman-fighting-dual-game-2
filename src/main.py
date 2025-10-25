import pygame
from game import Game
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS  # ensure settings.py exists

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

        # pass dt and events to game (adjust if your Game.update signature differs)
        game.update(dt, events)
        game.draw()
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()