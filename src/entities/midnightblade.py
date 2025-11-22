from .weapon import Weapon
class MidnightBlade(Weapon):
    name = "Midnight Blade"
    price = 300
    melee_bonus = 45
    cooldown = 250
    ranged = False
    def on_use(self, player, game):
        now = pygame.time.get_ticks()
        if now - getattr(player, "last_weapon_time", 0) < self.cooldown:
            return False
        player.attacking = True
        player.attack_type = "midnight"
        player.attack_duration = 320
        player.attack_start = now
        player.last_weapon_time = now
        return True


