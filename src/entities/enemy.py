class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.health = 100

    def move_towards_player(self, player_x, player_y):
        if self.x < player_x:
            self.x += 1  # Move right
        elif self.x > player_x:
            self.x -= 1  # Move left

        if self.y < player_y:
            self.y += 1  # Move down
        elif self.y > player_y:
            self.y -= 1  # Move up

    def attack(self):
        # Logic for attacking the player
        pass

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.die()

    def die(self):
        # Logic for enemy death
        pass