import pygame
import random
import time
import sys

# safe import of project settings (use defaults if a name is missing)
try:
    import settings as cfg
except Exception:
    cfg = None

def cfg_get(name, default):
    return getattr(cfg, name) if cfg and hasattr(cfg, name) else default

# visual / gameplay constants (use settings values when available)
SCREEN_BG = cfg_get("SCREEN_BG", (30, 30, 30))
PLAYER_SIZE = cfg_get("PLAYER_SIZE", (40, 80))
PLAYER_COLOR = cfg_get("PLAYER_COLOR", (50, 160, 255))
PLAYER_HIT_COLOR = cfg_get("PLAYER_HIT_COLOR", (255, 80, 80))
ENEMY_SIZE = cfg_get("ENEMY_SIZE", (40, 80))
ENEMY_COLOR = cfg_get("ENEMY_COLOR", (200, 60, 60))
GROUND_Y_OFFSET = cfg_get("GROUND_Y_OFFSET", 40)
GRAVITY = cfg_get("GRAVITY", 0.6)

PUNCH_COOLDOWN = cfg_get("PUNCH_COOLDOWN", 200)
PUNCH_DURATION = cfg_get("PUNCH_DURATION", 160)
KICK_COOLDOWN = cfg_get("KICK_COOLDOWN", 350)
KICK_DURATION = cfg_get("KICK_DURATION", 220)

SKILL_COOLDOWN = cfg_get("SKILL_COOLDOWN", 5000)
LASER_DAMAGE = cfg_get("LASER_DAMAGE", 100)
LASER_SPEED = cfg_get("LASER_SPEED", 12)
LASER_COLOR = cfg_get("LASER_COLOR", (255, 0, 200))
LASER_SIZE = cfg_get("LASER_SIZE", (6, 4))

MEDKIT_SIZE = cfg_get("MEDKIT_SIZE", (24, 14))
MEDKIT_COLOR = cfg_get("MEDKIT_COLOR", (180, 255, 180))
MEDKIT_FALL_MULTIPLIER = cfg_get("MEDKIT_FALL_MULTIPLIER", 0.5)
MEDKIT_HEAL = cfg_get("MEDKIT_HEAL", 80)

HEALTH_BG = cfg_get("HEALTH_BG", (60, 60, 60))
HEALTH_FG = cfg_get("HEALTH_FG", (80, 220, 100))

# --- Weapon system (kept inside this file per request - simple API) ---
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

class Gun(Weapon):
    name = "Gun"
    price = 100
    melee_bonus = 0
    cooldown = 600
    ranged = True
    def on_use(self, shooter, game):
        """Shoots from the shooter (player or enemy)."""
        now = pygame.time.get_ticks()
        if now - getattr(shooter, "last_weapon_time", 0) < self.cooldown:
            return False
        dir = 1 if getattr(shooter, "facing_right", True) else -1
        # fire two quick lasers with slight vertical offset
        for i in (-6, 6):
            pos = (shooter.rect.centerx + (shooter.width//2 + 6) * dir, shooter.rect.centery + i)
            l = Laser(pos, dir)
            game.projectiles.add(l)
            game.all_sprites.add(l)
        shooter.last_weapon_time = now
        return True

class Katana(Weapon):
    name = "Katana"
    price = 120
    melee_bonus = 18
    cooldown = 200
    ranged = False

class Flail(Weapon):
    name = "Flail"
    price = 140
    melee_bonus = 10
    cooldown = 400
    ranged = False

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

# --- Projectile / Entities ---
class Laser(pygame.sprite.Sprite):
    def __init__(self, pos, direction, damage=LASER_DAMAGE):
        super().__init__()
        self.image = pygame.Surface(LASER_SIZE)
        self.image.fill(LASER_COLOR)
        self.rect = self.image.get_rect(center=pos)
        self.vx = LASER_SPEED * direction
        self.life = 1200  # ms
        self.spawn_time = pygame.time.get_ticks()
        self.damage = damage

    def update(self, dt):
        self.rect.x += int(self.vx)
        if pygame.time.get_ticks() - self.spawn_time > self.life:
            self.kill()
        sw = pygame.display.get_surface().get_width()
        if self.rect.right < 0 or self.rect.left > sw:
            self.kill()

# --- Player with better stickman animation & weapon support ---
class Player(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.width, self.height = PLAYER_SIZE
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.rect = self.image.get_rect(midbottom=pos)
        self.vx = 0
        self.vy = 0
        self.on_ground = True
        self.facing_right = True
        self.max_hp = 1000
        self.hp = self.max_hp
        self.attacking = False
        self.attack_type = None
        self.attack_duration = 0
        self.attack_start = 0
        self.last_attack_time = 0
        self.last_skill_time = -SKILL_COOLDOWN
        self.has_knife = False

        # weapon system
        self.equipped_weapon = None
        self.attack_width_multiplier = 1.0
        self.anim_state = "idle"
        self.anim_timer = 0
        self.last_weapon_time = 0

    def equip(self, weapon):
        self.equipped_weapon = weapon
        if isinstance(weapon, Flail):
            self.attack_width_multiplier = 1.5
        elif isinstance(weapon, Katana):
            self.attack_width_multiplier = 1.3
        elif isinstance(weapon, MidnightBlade):
            self.attack_width_multiplier = 1.4
        else:
            self.attack_width_multiplier = 1.0

    def can_use_skill(self):
        return pygame.time.get_ticks() - self.last_skill_time >= SKILL_COOLDOWN

    def use_skill(self):
        self.last_skill_time = pygame.time.get_ticks()

    def start_attack(self, kind):
        now = pygame.time.get_ticks()
        if kind == "punch":
            dur = PUNCH_DURATION
        elif kind == "kick":
            dur = KICK_DURATION
        elif kind == "midnight":
            dur = getattr(self, "attack_duration", 300)
        else:
            dur = PUNCH_DURATION
        self.attacking = True
        self.attack_type = kind
        self.attack_duration = dur
        self.attack_start = now
        self.last_attack_time = now
        self.anim_state = "attack"

    def update(self, dt, game=None):
        keys = pygame.key.get_pressed()
        self.vx = 0
        if keys[pygame.K_a]:
            self.vx = -4
            self.facing_right = False
            if self.on_ground:
                self.anim_state = "run"
        elif keys[pygame.K_d]:
            self.vx = 4
            self.facing_right = True
            if self.on_ground:
                self.anim_state = "run"
        else:
            if self.on_ground and not self.attacking:
                self.anim_state = "idle"

        if keys[pygame.K_w] and self.on_ground:
            self.vy = -12
            self.on_ground = False
            self.anim_state = "jump"

        now = pygame.time.get_ticks()

        # weapon fire / melee mapping: V triggers weapon or punch
        if keys[pygame.K_v] and now - self.last_attack_time > PUNCH_COOLDOWN:
            if self.equipped_weapon and getattr(self.equipped_weapon, "ranged", False):
                used = self.equipped_weapon.on_use(self, game)
                if used:
                    self.anim_state = "attack"
            else:
                self.start_attack("punch")

        if keys[pygame.K_x] and now - self.last_attack_time > KICK_COOLDOWN:
            self.start_attack("kick")

        # finish attack by duration
        if self.attacking and now - self.attack_start > self.attack_duration:
            self.attacking = False
            self.attack_type = None
            if self.anim_state == "attack":
                self.anim_state = "idle"

        # physics
        self.rect.x += int(self.vx)
        self.vy += GRAVITY
        self.rect.y += int(self.vy)
        ground_y = pygame.display.get_surface().get_height() - GROUND_Y_OFFSET
        if self.rect.bottom >= ground_y:
            self.rect.bottom = ground_y
            self.vy = 0
            self.on_ground = True

    def get_attack_rect(self):
        if not self.attacking:
            return None
        w = int((24 if self.attack_type == "punch" else 40) * self.attack_width_multiplier)
        if self.attack_type == "midnight":
            w = int(80 * self.attack_width_multiplier)
            h = 36
        else:
            h = 20
        if self.facing_right:
            ax = self.rect.right
        else:
            ax = self.rect.left - w
        ay = self.rect.centery - h // 2
        return pygame.Rect(ax, ay, w, h)

    def draw_weapon(self, surf, hand_pos):
        # draw weapon shape near hand_pos depending on equipped_weapon
        if not self.equipped_weapon:
            return
        name = self.equipped_weapon.name
        x, y = hand_pos
        color = (200, 200, 200)
        if name == "Gun":
            # barrel and grip
            barrel = pygame.Rect(0, 0, 34, 8)
            barrel.center = (x + (18 if self.facing_right else -18), y)
            grip = pygame.Rect(0, 0, 8, 12)
            grip.center = (x + (6 if self.facing_right else -6), y + 8)
            pygame.draw.rect(surf, (30,30,30), barrel)
            pygame.draw.rect(surf, (60,60,60), grip)
            pygame.draw.rect(surf, (200,200,40), barrel.inflate(-10,-2), 0)
        elif name == "Katana":
            # long thin blade
            blade_len = 60
            bx = x + (blade_len//2 if self.facing_right else -blade_len//2)
            pygame.draw.line(surf, (220,220,255), (x, y), (bx, y-6), 4)
            pygame.draw.rect(surf, (80,40,20), (x - 6, y - 4, 12, 8))
        elif name == "Flail":
            # chain + ball
            bx = x + (22 if self.facing_right else -22)
            pygame.draw.line(surf, (120,120,120), (x, y), (bx, y+6), 3)
            pygame.draw.circle(surf, (40,40,40), (int(bx), int(y+8)), 10)
        elif name == "Midnight Blade":
            bx = x + (34 if self.facing_right else -34)
            pygame.draw.line(surf, (30,30,30), (x, y), (bx, y-4), 6)
            pygame.draw.line(surf, (120,0,200), (x, y-2), (bx, y-6), 3)

    def draw(self, surf):
        # draw improved stickman with swinging arm animation
        x = self.rect.centerx
        top = self.rect.top
        bottom = self.rect.bottom
        body_color = PLAYER_COLOR
        head_r = int(self.width * 0.18)
        head_center = (x, top + head_r + 2)
        neck_y = head_center[1] + head_r
        hip_y = bottom - int(self.height * 0.2)

        # calculate attack progress for smooth swing
        now = pygame.time.get_ticks()
        atk_prog = 0.0
        if self.attacking:
            atk_prog = min(1.0, (now - self.attack_start) / max(1, self.attack_duration))

        if self.attacking:
            body_color = PLAYER_HIT_COLOR

        # head
        pygame.draw.circle(surf, body_color, head_center, head_r, 0)
        # torso (slight recoil on attack)
        recoil = int(6 * atk_prog) if self.attacking else 0
        pygame.draw.line(surf, body_color, (x, neck_y), (x, hip_y + recoil), 4)

        # arms: compute hand positions using simple swing math
        arm_len = 28
        shoulder = (x, neck_y + 2)
        # attack swing angle [-45..45] degrees converted to offset
        swing = int(30 * (1 - (atk_prog * 2 - 1)**2)) if self.attacking else (6 if self.anim_state == "run" else 0)
        if self.facing_right:
            hand_x = shoulder[0] + arm_len + int(swing * (1 if self.attacking else 0))
        else:
            hand_x = shoulder[0] - arm_len - int(swing * (1 if self.attacking else 0))
        hand_y = shoulder[1] + (6 if self.attacking else 14)
        # draw non-attacking opposite arm
        opp_x = shoulder[0] - (arm_len // 2 if self.facing_right else -arm_len//2)
        opp_y = shoulder[1] + 16
        pygame.draw.line(surf, body_color, shoulder, (opp_x, opp_y), 4)
        # draw main arm (attacking)
        pygame.draw.line(surf, body_color, shoulder, (hand_x, hand_y), 4)

        # draw weapon in hand if any
        self.draw_weapon(surf, (hand_x, hand_y))

        # legs
        pygame.draw.line(surf, body_color, (x, hip_y + recoil), (x - 10, bottom), 4)
        pygame.draw.line(surf, body_color, (x, hip_y + recoil), (x + 10, bottom), 4)

# --- Enemy stickman remains procedural as before ---
class Enemy(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.width, self.height = ENEMY_SIZE
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.rect = self.image.get_rect(midbottom=pos)
        self.vx = 0
        self.vy = 0
        self.on_ground = True
        self.facing_right = False
        self.max_hp = 1000
        self.hp = self.max_hp
        self.attacking = False
        self.attack_type = None
        self.last_action_time = pygame.time.get_ticks()
        self.next_action_delay = random.randint(600, 1400)
        self.attack_end_timer = None
        # enemy may equip a weapon (includes Gun so it can shoot)
        self.equipped_weapon = random.choice([None, Gun(), Katana(), Flail(), None])
        self.last_weapon_time = 0

    def update(self, dt, player_rect=None, game=None):
        now = pygame.time.get_ticks()
        if player_rect:
            if abs(self.rect.centerx - player_rect.centerx) > 60:
                self.vx = 2 if player_rect.centerx > self.rect.centerx else -2
                self.facing_right = self.vx > 0
            else:
                self.vx = 0

        self.rect.x += self.vx
        self.vy += GRAVITY
        self.rect.y += int(self.vy)
        ground_y = pygame.display.get_surface().get_height() - GROUND_Y_OFFSET
        if self.rect.bottom >= ground_y:
            self.rect.bottom = ground_y
            self.vy = 0
            self.on_ground = True

        if now - self.last_action_time > self.next_action_delay:
            self.last_action_time = now
            self.next_action_delay = random.randint(700, 1600)
            if random.random() < 0.6:
                self.attacking = True
                self.attack_type = random.choice(["punch", "kick"])
                self.attack_end_timer = now + 220

        if self.attack_end_timer and now > self.attack_end_timer:
            self.finish_attack()
            self.attack_end_timer = None

        # If enemy has a ranged weapon, occasionally shoot at the player
        if self.equipped_weapon and getattr(self.equipped_weapon, "ranged", False) and game and player_rect:
            dist = abs(self.rect.centerx - player_rect.centerx)
            # preference to shoot when within range; small random chance each update
            if dist < 450 and random.random() < 0.02:
                self.equipped_weapon.on_use(self, game)

    def finish_attack(self):
        self.attacking = False
        self.attack_type = None

    def get_attack_rect(self):
        if not self.attacking:
            return None
        w = 24 if self.attack_type == "punch" else 40
        h = 20
        if self.facing_right:
            ax = self.rect.right
        else:
            ax = self.rect.left - w
        ay = self.rect.centery - h // 2
        return pygame.Rect(ax, ay, w, h)

    def draw(self, surf):
        x = self.rect.centerx
        top = self.rect.top
        bottom = self.rect.bottom
        body_color = ENEMY_COLOR if not self.attacking else (255, 140, 140)
        head_r = int(self.width * 0.18)
        head_center = (x, top + head_r + 2)
        neck_y = head_center[1] + head_r
        hip_y = bottom - int(self.height * 0.2)
        pygame.draw.circle(surf, body_color, head_center, head_r, 0)
        pygame.draw.line(surf, body_color, (x, neck_y), (x, hip_y), 4)
        # arms
        if self.attacking:
            if self.facing_right:
                pygame.draw.line(surf, body_color, (x, neck_y), (x + 30, neck_y + 10), 4)
            else:
                pygame.draw.line(surf, body_color, (x, neck_y), (x - 30, neck_y + 10), 4)
        else:
            pygame.draw.line(surf, body_color, (x, neck_y), (x - 12, neck_y + 18), 4)
            pygame.draw.line(surf, body_color, (x, neck_y), (x + 12, neck_y + 18), 4)
        # draw enemy weapon if present
        if self.equipped_weapon:
            # simple katana/flail visuals
            hand = (x + (18 if self.facing_right else -18), neck_y + 10)
            name = self.equipped_weapon.name
            if name == "Katana":
                bx = hand[0] + (34 if self.facing_right else -34)
                pygame.draw.line(surf, (220,220,255), hand, (bx, hand[1]-6), 4)
            elif name == "Flail":
                bx = hand[0] + (22 if self.facing_right else -22)
                pygame.draw.line(surf, (120,120,120), hand, (bx, hand[1]+6), 3)
                pygame.draw.circle(surf, (40,40,40), (int(bx), int(hand[1]+8)), 8)
        # legs
        pygame.draw.line(surf, body_color, (x, hip_y), (x - 10, bottom), 4)
        pygame.draw.line(surf, body_color, (x, hip_y), (x + 10, bottom), 4)

class MedKit(pygame.sprite.Sprite):
    def __init__(self, x, top_y=-10):
        super().__init__()
        self.image = pygame.Surface(MEDKIT_SIZE)
        self.image.fill(MEDKIT_COLOR)
        self.rect = self.image.get_rect(midtop=(x, top_y))
        self.vy = 0

    def update(self, dt):
        self.vy += GRAVITY * MEDKIT_FALL_MULTIPLIER
        self.rect.y += int(self.vy)
        screen_h = pygame.display.get_surface().get_height()
        if self.rect.top > screen_h:
            self.kill()

# --- Game manager simplified: no shop, number-bar equips weapons ---
class Game:
    def __init__(self, screen):
        self.screen = screen
        self.screen_rect = screen.get_rect()
        self.bg_color = SCREEN_BG
        self.all_sprites = pygame.sprite.Group()  # pickups & projectiles included here
        ground_y = self.screen_rect.height - GROUND_Y_OFFSET
        self.player = Player((100, ground_y))
        self.enemy = Enemy((self.screen_rect.width - 100, ground_y))
        self.all_sprites.add(self.enemy)  # enemy remains in sprites for collisions if needed
        self.font = pygame.font.SysFont(None, 24)

        self.items = pygame.sprite.Group()
        self.last_medkit_time = pygame.time.get_ticks()
        self.next_medkit_delay = random.randint(5000, 12000)

        self.projectiles = pygame.sprite.Group()

        self.coins = 0
        self.state = "running"  # only running or gameover

    def spawn_medkit(self):
        x = random.randint(40, self.screen_rect.width - 40)
        med = MedKit(x)
        self.items.add(med)
        self.all_sprites.add(med)

    def spawn_laser(self, direction, damage=LASER_DAMAGE):
        pos = (self.player.rect.centerx + (self.player.width//2 + 6) * (1 if direction>0 else -1),
               self.player.rect.centery)
        l = Laser(pos, direction, damage=damage)
        self.projectiles.add(l)
        self.all_sprites.add(l)

    def restart(self):
        ground_y = self.screen_rect.height - GROUND_Y_OFFSET
        self.player.rect.midbottom = (100, ground_y)
        self.player.hp = self.player.max_hp
        self.player.has_knife = False
        self.player.equipped_weapon = None
        self.enemy.rect.midbottom = (self.screen_rect.width - 100, ground_y)
        self.enemy.hp = self.enemy.max_hp
        self.items.empty()
        self.projectiles.empty()
        self.all_sprites = pygame.sprite.Group(self.enemy)
        self.state = "running"

    def update(self, dt, events):
        # handle inputs: numbers 1-4 equip weapons instantly while running
        for ev in events:
            if ev.type == pygame.KEYDOWN:
                if self.state == "gameover":
                    if ev.key == pygame.K_r:
                        self.restart()
                else:
                    # choose weapons with number bar:
                    if ev.key == pygame.K_1:
                        self.player.equip(Gun())
                    elif ev.key == pygame.K_2:
                        self.player.equip(Katana())
                    elif ev.key == pygame.K_3:
                        self.player.equip(Flail())
                    elif ev.key == pygame.K_4:
                        self.player.equip(MidnightBlade())
                    elif ev.key == pygame.K_0:
                        self.player.equip(None)
                    elif ev.key == pygame.K_SPACE and self.player.can_use_skill():
                        dir = 1 if self.player.facing_right else -1
                        self.spawn_laser(dir)
                        self.player.use_skill()

        if self.state != "running":
            return

        self.player.update(dt, game=self)
        self.enemy.update(dt, player_rect=self.player.rect, game=self)
        self.items.update(dt)
        self.projectiles.update(dt)

        now = pygame.time.get_ticks()
        if now - self.last_medkit_time > self.next_medkit_delay:
            self.last_medkit_time = now
            self.next_medkit_delay = random.randint(8000, 15000)
            self.spawn_medkit()

        # player melee collision
        pr = self.player.get_attack_rect()
        if pr and pr.colliderect(self.enemy.rect) and pygame.time.get_ticks() - self.player.last_attack_time < 300:
            base = 10 if self.player.attack_type == "punch" else 12
            if self.player.equipped_weapon:
                dmg = self.player.equipped_weapon.melee_damage(base)
            elif self.player.has_knife:
                dmg = base * 2
            else:
                dmg = base
            self.enemy.hp = max(0, self.enemy.hp - dmg)
            self.coins += 10
            if self.player.facing_right:
                self.enemy.rect.x += 10
            else:
                self.enemy.rect.x -= 10

        # enemy attack hurts player
        er = self.enemy.get_attack_rect()
        if er and er.colliderect(self.player.rect) and self.enemy.attack_end_timer and pygame.time.get_ticks() - (self.enemy.attack_end_timer - 220) < 80:
            self.player.hp = max(0, self.player.hp - (10 if self.enemy.attack_type == "kick" else 6))

        # projectiles vs enemy
        for laser in list(self.projectiles):
            if laser.rect.colliderect(self.enemy.rect):
                self.enemy.hp = max(0, self.enemy.hp - laser.damage)
                laser.kill()
                self.coins += 20

        # pickups
        picked = pygame.sprite.spritecollide(self.player, self.items, dokill=True)
        if picked:
            for _ in picked:
                self.player.hp = min(self.player.max_hp, self.player.hp + MEDKIT_HEAL)

        if self.player.hp <= 0:
            self.state = "gameover"

        if self.enemy.hp <= 0:
            self.coins += 50
            self.enemy.hp = self.enemy.max_hp
            ground_y = self.screen_rect.height - GROUND_Y_OFFSET
            self.enemy.rect.midbottom = (self.screen_rect.width - 100, ground_y)

    def draw(self):
        self.screen.fill(self.bg_color)
        ground_y = self.screen_rect.height - GROUND_Y_OFFSET
        pygame.draw.line(self.screen, (80, 80, 80), (0, ground_y), (self.screen_rect.width, ground_y), 4)

        # draw pickups & projectiles
        self.all_sprites.draw(self.screen)

        # draw enemy and player procedurally
        self.enemy.draw(self.screen)
        self.player.draw(self.screen)

        # debug: draw attack rects
        ar = self.player.get_attack_rect()
        if ar:
            pygame.draw.rect(self.screen, (255, 200, 0), ar, 2)
        er = self.enemy.get_attack_rect()
        if er:
            pygame.draw.rect(self.screen, (255, 200, 50), er, 2)

        # HUD: coins, weapon, skill cd
        self._draw_health_bar(self.player.hp, self.player.max_hp, 20, 20, 300, 20)
        self._draw_health_bar(self.enemy.hp, self.enemy.max_hp, self.screen_rect.width - 320, 20, 300, 20)
        coin_txt = self.font.render(f"Coins: {self.coins}", True, (255, 215, 0))
        self.screen.blit(coin_txt, (20, 50))

        weapon_text = self.player.equipped_weapon.name if self.player.equipped_weapon else ("Knife" if self.player.has_knife else "Fist")
        self.screen.blit(self.font.render(f"Weapon: {weapon_text}  (1:Gun 2:Katana 3:Flail 4:Midnight 0:None)", True, (255,255,255)), (20, 80))
        cd = max(0, SKILL_COOLDOWN - (pygame.time.get_ticks() - self.player.last_skill_time))
        cd_s = f"{cd//1000}.{(cd%1000)//100}s" if cd>0 else "Ready"
        self.screen.blit(self.font.render(f"Skill (SPACE): Laser - {cd_s}", True, (255,255,255)), (20, 100))

        if self.state == "gameover":
            self._draw_overlay("GAME OVER - Press R to Restart")

    def _draw_health_bar(self, hp, max_hp, x, y, w, h):
        pygame.draw.rect(self.screen, HEALTH_BG, (x, y, w, h))
        pct = max(0, hp) / max_hp
        pygame.draw.rect(self.screen, HEALTH_FG, (x, y, int(w * pct), h))
        txt = self.font.render(f"{hp}/{max_hp}", True, (255,255,255))
        self.screen.blit(txt, (x + w//2 - txt.get_width()//2, y + h//2 - txt.get_height()//2))

    def _draw_overlay(self, text):
        s = pygame.Surface((self.screen_rect.width, self.screen_rect.height), pygame.SRCALPHA)
        s.fill((0,0,0,180))
        self.screen.blit(s, (0,0))
        txt = self.font.render(text, True, (255,255,255))
        self.screen.blit(txt, (self.screen_rect.width//2 - txt.get_width()//2, self.screen_rect.height//2 - 10))