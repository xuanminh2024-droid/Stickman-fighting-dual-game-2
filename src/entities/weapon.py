class Weapon:
    name = "Fist"
    price = 0
    melee_bonus = 0
    cooldown = 300
    ranged = False
    def on_use(self, player, game):
        """Ranged use or special action. Return True if consumed/triggered."""
        return False
    def melee_damage(self, base):
        return base + self.melee_bonus
