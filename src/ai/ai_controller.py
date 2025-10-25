class AIController:
    def __init__(self, enemy):
        self.enemy = enemy

    def update(self, player):
        if self.enemy.health > 0:
            self.move_towards_player(player)
            if self.should_attack():
                self.enemy.attack()

    def move_towards_player(self, player):
        if player.rect.x < self.enemy.rect.x:
            self.enemy.move_left()
        elif player.rect.x > self.enemy.rect.x:
            self.enemy.move_right()

    def should_attack(self):
        # Randomly decide whether to attack
        import random
        return random.random() < 0.1  # 10% chance to attack each update