class Menu:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 74)
        self.options = ["Start Game", "Options", "Quit"]
        self.selected_option = 0

    def draw(self):
        self.screen.fill((0, 0, 0))
        for index, option in enumerate(self.options):
            if index == self.selected_option:
                text = self.font.render(option, True, (255, 0, 0))
            else:
                text = self.font.render(option, True, (255, 255, 255))
            text_rect = text.get_rect(center=(self.screen.get_width() // 2, 200 + index * 100))
            self.screen.blit(text, text_rect)
        pygame.display.flip()

    def move_selection(self, direction):
        self.selected_option += direction
        if self.selected_option < 0:
            self.selected_option = len(self.options) - 1
        elif self.selected_option >= len(self.options):
            self.selected_option = 0

    def select_option(self):
        if self.selected_option == 0:
            return "start_game"
        elif self.selected_option == 1:
            return "options"
        elif self.selected_option == 2:
            return "quit"