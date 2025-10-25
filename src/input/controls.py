class Controls:
    def __init__(self):
        self.key_map = {
            'left': pygame.K_a,
            'right': pygame.K_d,
            'jump': pygame.K_w,
            'crouch': pygame.K_s,
            'kick': pygame.K_j,
            'punch': pygame.K_k
        }

    def get_controls(self):
        return self.key_map

    def handle_input(self, player):
        keys = pygame.key.get_pressed()
        
        if keys[self.key_map['left']]:
            player.move_left()
        if keys[self.key_map['right']]:
            player.move_right()
        if keys[self.key_map['jump']]:
            player.jump()
        if keys[self.key_map['crouch']]:
            player.crouch()
        if keys[self.key_map['kick']]:
            player.kick()
        if keys[self.key_map['punch']]:
            player.punch()