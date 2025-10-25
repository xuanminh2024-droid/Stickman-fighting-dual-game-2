class HUD:
    def __init__(self, screen, player_health, enemy_health):
        self.screen = screen
        self.player_health = player_health
        self.enemy_health = enemy_health
        self.font = pygame.font.Font(None, 36)

    def draw(self):
        player_health_text = self.font.render(f'Player Health: {self.player_health}', True, (255, 255, 255))
        enemy_health_text = self.font.render(f'Enemy Health: {self.enemy_health}', True, (255, 255, 255))
        
        self.screen.blit(player_health_text, (10, 10))
        self.screen.blit(enemy_health_text, (10, 50))

    def update_health(self, player_health, enemy_health):
        self.player_health = player_health
        self.enemy_health = enemy_health