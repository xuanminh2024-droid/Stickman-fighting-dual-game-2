import pygame
import random
import time
import sys
import math
from entities.player import Player 
from entities.flail import Flail
from entities.katana import Katana
from entities.midnightblade import MidnightBlade
from entities.weapon import Weapon
# safe import of project settings (use defaults if a name is missing)
try:
    import settings
except Exception:
    settings = None

def cfg_get(name, default):
    if settings is None:
        return default
    return getattr(settings, name, default)

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
# set laser damage to 10 as requested
LASER_DAMAGE = cfg_get("LASER_DAMAGE", 10)
LASER_SPEED = cfg_get("LASER_SPEED", 12)
LASER_COLOR = cfg_get("LASER_COLOR", (255, 60, 200))
LASER_SIZE = cfg_get("LASER_SIZE", (20, 6))

MEDKIT_SIZE = cfg_get("MEDKIT_SIZE", (24, 14))
MEDKIT_COLOR = cfg_get("MEDKIT_COLOR", (180, 255, 180))
MEDKIT_FALL_MULTIPLIER = cfg_get("MEDKIT_FALL_MULTIPLIER", 0.5)
MEDKIT_HEAL = cfg_get("MEDKIT_HEAL", 80)

HEALTH_BG = cfg_get("HEALTH_BG", (60, 60, 60))
HEALTH_FG = cfg_get("HEALTH_FG", (80, 220, 100))


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
        # fire two quick lasers with slight vertical offset; use LASER_DAMAGE (10)
        for i in (-6, 6):
            pos = (shooter.rect.centerx + (shooter.width//2 + 6) * dir, shooter.rect.centery + i)
            l = Laser(pos, dir, damage=LASER_DAMAGE)
            game.projectiles.add(l)
            game.all_sprites.add(l)
        shooter.last_weapon_time = now
        return True


# --- Projectile / Entities ---
class Laser(pygame.sprite.Sprite):
    def __init__(self, pos, direction, damage=LASER_DAMAGE):
        super().__init__()
        w, h = LASER_SIZE
        w = max(w, 18)
        h = max(h, 4)
        # create a glow / beam image
        surf = pygame.Surface((w*3, h*6), pygame.SRCALPHA)
        center = (surf.get_width() // 2, surf.get_height() // 2)
        base_color = LASER_COLOR
        # layered glow (fixed center-y typo)
        for i, alpha in enumerate((40, 90, 160, 230), start=4):
            radius_x = int((w/2 + i*3))
            radius_y = int((h/2 + i*1.6))
            col = (*base_color[:3], max(6, alpha//i))
            pygame.draw.ellipse(surf, col, (center[0]-radius_x, center[1]-radius_y, radius_x*2, radius_y*2))
        # bright core
        core_rect = pygame.Rect(0,0,w, h)
        core_rect.center = center
        pygame.draw.rect(surf, base_color, core_rect)
        # thin white edge
        pygame.draw.rect(surf, (255,255,255), core_rect.inflate(-2,-1), 1)

        self.image = surf
        # place rect so center aligns with pos
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
        # enemy may randomly equip a weapon visually (not functional)
        self.equipped_weapon = random.choice([None, Katana(), Flail(), None, None])

    def update(self, dt, player_rect=None):
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

        # animated fire background params
        self.fire_height = 160
        self._fire_seed = random.randint(0, 9999)

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
        self.enemy.update(dt, player_rect=self.player.rect)
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

    def _draw_fire_background(self):
        """Draw a war-themed animated background: smoky sky, distant explosions, ruins silhouette and embers."""
        w = self.screen_rect.width
        h = self.screen_rect.height
        t = pygame.time.get_ticks() * 0.0015
        base_y = h

        # 1) dark gradient sky (reddish/orange near horizon -> dark smoky above)
        sky = pygame.Surface((w, h), pygame.SRCALPHA)
        for y in range(h):
            # blend from deep orange near horizon to near-black
            p = y / h
            r = int(20 + (220 - 20) * (1 - p) * 0.8)
            g = int(12 + (80 - 12) * (1 - p) * 0.6)
            b = int(18 + (40 - 18) * (1 - p) * 0.3)
            a = int(200 * (1 - p))
            sky.fill((r, g, b, a), rect=pygame.Rect(0, y, w, 1))
        self.screen.blit(sky, (0, 0))

        # 2) distant explosions / glows (pulsing orange spots)
        for i, posx in enumerate(range(80, w, 220)):
            phase = (t * (0.6 + (i % 3) * 0.15) + (i * 0.7) + (self._fire_seed % 37)) % (2 * math.pi)
            intensity = 0.5 + 0.5 * math.sin(phase)
            glow_r = int(60 + 40 * intensity)
            glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
            gx = posx + (math.sin(t * 0.8 + i) * 60)
            gy = int(h * 0.72 - abs(math.cos(t * 0.6 + i)) * 30)
            color = (255, int(120 + 80 * intensity), 30, int(80 + 140 * intensity))
            pygame.draw.ellipse(glow_surf, color, (0, 0, glow_r * 2, glow_r * 2))
            self.screen.blit(glow_surf, (gx - glow_r, gy - glow_r), special_flags=0)

        # 3) ruined city silhouette (solid dark shapes with slight flicker)
        silhouette = pygame.Surface((w, int(h * 0.45)), pygame.SRCALPHA)
        sil_h = silhouette.get_height()
        # build skyline with rectangles of varying height
        x = 0
        rng = int(self._fire_seed % 97)
        while x < w:
            bw = 30 + ((x + rng) % 90)
            bh = int(sil_h * (0.35 + ((x * 13 + rng) % 60) / 100))
            color_dark = (18, 18, 20, 255)
            rect = pygame.Rect(x, sil_h - bh, bw, bh)
            pygame.draw.rect(silhouette, color_dark, rect)
            # occasional broken tower tops
            if ((x + rng) % 130) < 20:
                pygame.draw.rect(silhouette, (34, 20, 20, 255), (x + bw//4, sil_h - bh - 6, bw//2, 6))
            x += bw + 6
        # slight horizontal jitter to simulate heat/smoke distortion
        jitter_x = int(math.sin(t * 0.9 + self._fire_seed) * 2)
        self.screen.blit(silhouette, (jitter_x, int(h * 0.45)), special_flags=0)

        # 4) layered smoke plumes (soft semi-transparent clouds rising)
        smoke_layers = 3
        for layer in range(smoke_layers):
            layer_surf = pygame.Surface((w, int(h * 0.35)), pygame.SRCALPHA)
            base_y_off = int(h * 0.35 * layer * 0.25)
            for i in range(12):
                px = int(((i * 97 + self._fire_seed * 3) % (w + 200)) - 100 + math.sin(t * (0.3 + layer * 0.15) + i) * 80)
                py = int(base_y_off + (i % 5) * 18 + math.cos(t * 0.4 + i * 0.6 + layer) * 12)
                rad = int(40 + 30 * layer + (i % 4) * 6)
                col = (40, 40, 48, max(12, 60 - layer * 8))
                pygame.draw.ellipse(layer_surf, col, (px % w, py, rad, int(rad * 0.7)))
            # blur effect by drawing offset copies
            for ox, oy, a in ((0, 0, 140), (6, -4, 40), (-6, 3, 30)):
                tmp = layer_surf.copy()
                tmp.fill((255, 255, 255, a), special_flags=pygame.BLEND_RGBA_MULT)
                self.screen.blit(tmp, (ox, int(h * 0.36) - base_y_off//2 + oy), special_flags=0)

        # 5) embers rising (small bright particles)
        ember_count = 42
        for i in range(ember_count):
            phase = (i * 0.37 + t * (0.8 + (i % 5) * 0.05) + (self._fire_seed % 13)) 
            ex = int((w * ((i * 23 + 17) % 97)) / 100 + math.sin(phase) * 90) % w
            ey = int(h * 0.8 - ( (math.fmod(phase * 10, 300)) ) * 0.6)
            size = max(1, int(2 + (math.sin(phase * 3 + i) + 1) * 2))
            ember_col = (255, 200 - (i % 6) * 20, 60, 220)
            pygame.draw.circle(self.screen, ember_col, (ex, ey), size)

        # 6) ground glow / scorched earth strip
        glow_h = int(h * 0.12)
        ground_glow = pygame.Surface((w, glow_h), pygame.SRCALPHA)
        for y in range(glow_h):
            a = int(190 * (1 - (y / glow_h)) )
            ground_glow.fill((100 + int(120 * (1 - y/glow_h)), 40, 15, a), rect=pygame.Rect(0, y, w, 1))
        self.screen.blit(ground_glow, (0, h - glow_h))

    def draw(self):
        # draw animated fire background first
        try:
            self._draw_fire_background()
        except Exception:
            # fallback to plain fill if anything fails
            self.screen.fill(self.bg_color)
        # draw ground line and rest
        ground_y = self.screen_rect.height - GROUND_Y_OFFSET
        pygame.draw.line(self.screen, (80, 80, 80), (0, ground_y), (self.screen_rect.width, ground_y), 4)

        # draw pickups & projectiles (projectiles contain laser sprite with glow)
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