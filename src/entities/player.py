class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.health = 100
        self.is_jumping = False
        self.is_crouching = False
        self.animations = {
            'idle': None,
            'run': None,
            'jump': None,
            'crouch': None,
            'kick': None,
            'punch': None
        }

    def move_left(self):
        self.x -= 5  # Move left by 5 pixels

    def move_right(self):
        self.x += 5  # Move right by 5 pixels

    def jump(self):
        if not self.is_jumping:
            self.is_jumping = True
            # Logic for jumping

    def crouch(self):
        self.is_crouching = True
        # Logic for crouching

    def kick(self):
        # Logic for kicking
        pass

    def punch(self):
        # Logic for punching
        pass

    def update(self):
        # Update player state and animations
        pass

    def draw(self, surface):
        # Draw the player on the given surface
        pass