import pygame
from .flail import Flail
from .katana import Katana
import math
from .midnightblade import MidnightBlade
try:
    import settings
except Exception:
    settings = None

def cfg_get(name, default):
    if settings is None:
        return default
    return getattr(settings, name, default)
GRAVITY = cfg_get("GRAVITY", 0.6)
GROUND_Y_OFFSET = cfg_get("GROUND_Y_OFFSET", 40)
PLAYER_SIZE = cfg_get("PLAYER_SIZE", (40, 80))
PLAYER_COLOR = cfg_get("PLAYER_COLOR", (50, 160, 255))
PLAYER_HIT_COLOR = cfg_get("PLAYER_HIT_COLOR", (255, 80, 80))
SKILL_COOLDOWN = cfg_get("SKILL_COOLDOWN", 5000)
KICK_COOLDOWN = cfg_get("KICK_COOLDOWN", 350)
KICK_DURATION = cfg_get("KICK_DURATION", 220)
PUNCH_COOLDOWN = cfg_get("PUNCH_COOLDOWN",300)
PUNCH_DURATION =cfg_get("PUNCH_DURATION",180)

# set laser damage to 10 as requested


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
        self.goku_img = pygame.image.load("Stickman fight/street-duel/src/images/Goku.png").convert_alpha()
        self.goku_base = self.goku_img

        # scale theo kích thước player
        h = self.rect.height
        scale_factor = h / self.goku_img.get_height()
        w = int(self.goku_img.get_width() * scale_factor)
        self.goku_img = pygame.transform.scale(self.goku_img, (w, h))



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

        def _draw_midnight_blade(surf, hx, hy, facing_right=True, size=1.0, animated=True):
            flip = 1 if facing_right else -1
            s = float(size)
            blade_len = int(78 * s)
            blade_w = max(6, int(12 * s))
            base_x = hx
            tip_x = hx + flip * blade_len

            # build tapered blade polygon (upper edge then lower)
            segments = 8
            upper = []
            lower = []
            for i in range(segments + 1):
                t = i / segments
                bx = int(hx + flip * (t * blade_len))
                # gentle taper and slight concave profile
                taper = int((1 - t) * (blade_w // 2))
                curve = int(math.sin(t * math.pi) * 2 * s)
                uy = int(hy - taper - curve - t * int(6 * s))
                ly = int(hy + taper + curve + t * int(6 * s))
                upper.append((bx, uy))
                lower.append((bx, ly))
            blade_poly = upper + lower[::-1]

            # core
            pygame.draw.polygon(surf, (60, 60, 70), blade_poly)
            # bevel highlight along upper edge
            if len(upper) >= 2:
                pygame.draw.lines(surf, (200, 200, 220), False, upper, max(1, int(2 * s)))
            # thin dark edge near lower side
            if len(lower) >= 2:
                pygame.draw.lines(surf, (30,30,36), False, lower, max(1, int(1 * s)))

            # fuller (central groove)
            fpts = []
            for i in range(4):
                tt = i / 3
                fx = int(hx + flip * (tt * (blade_len - 12 * s)))
                fy = int(hy + math.sin(tt * math.pi) * int(2 * s))
                fpts.append((fx, fy))
            pygame.draw.lines(surf, (30,30,40), False, fpts, max(1, int(2 * s)))
            pygame.draw.lines(surf, (120,120,140), False, fpts, max(1, int(1 * s)))

            # ornate guard (tsuba)
            guard_w = int(14 * s)
            guard_h = int(6 * s)
            pygame.draw.ellipse(surf, (80,60,55), (hx - guard_w//2, hy - guard_h//2, guard_w, guard_h))
            pygame.draw.ellipse(surf, (140,110,90), (hx - guard_w//4, hy - guard_h//4, guard_w//2, guard_h//2))

            # handle
            handle_len = int(20 * s)
            handle_w = int(8 * s)
            handle_rect = pygame.Rect(0,0, handle_w, handle_len)
            handle_rect.center = (int(hx - flip * (handle_w//2 + 2)), int(hy + handle_len/2))
            pygame.draw.rect(surf, (30,30,36), handle_rect)
            pygame.draw.rect(surf, (90,60,40), handle_rect, max(1, int(1*s)))
            # wrap texture
            step = int(5 * s)
            for off in range(-step*2, handle_len + step*2, step):
                sx = handle_rect.left + (off if facing_right else (handle_rect.width - off))
                pygame.draw.line(surf, (20,20,24), (sx, handle_rect.top + off), (sx + flip * step, handle_rect.bottom + off), max(1, int(1*s)))

            # pommel
            pom_x = int(handle_rect.centerx - flip * (handle_w//2 + 2))
            pom_y = int(handle_rect.bottom + int(3 * s))
            pygame.draw.circle(surf, (120,100,80), (pom_x, pom_y), max(3, int(3 * s)))
            pygame.draw.circle(surf, (200,180,150), (pom_x, pom_y), max(1, int(1 * s)))

            # subtle purple veins and tip glow
            vein_col = (160, 60, 180)
            vx1 = int(hx + flip * int(14 * s))
            vx2 = int(tip_x - flip * int(18 * s))
            pygame.draw.aaline(surf, vein_col, (vx1, hy - int(2*s)), (vx2, hy + int(2*s)))
            if animated:
                pulse = 0.5 + 0.5 * abs(math.sin(pygame.time.get_ticks() * 0.006))
            else:
                pulse = 0.6
            glow_r = int(6 * s * pulse)
            glow = pygame.Surface((glow_r*4, glow_r*2), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (180,70,200,int(100 * pulse)), (0,0, glow.get_width(), glow.get_height()))
            surf.blit(glow, (tip_x - glow.get_width()//2 + (-4 if facing_right else 4), hy - glow.get_height()//2), special_flags=pygame.BLEND_RGBA_ADD)

        # existing weapon drawings
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
            _draw_midnight_blade(surf, x + (8 if self.facing_right else -8), y, self.facing_right, size=1.0, animated=True)
    def draw(self, surf):
        # ------------------------------------------------------
        # Basic info
        # ------------------------------------------------------
        x = self.rect.centerx
        y = self.rect.centery
        top = self.rect.top
        bottom = self.rect.bottom

        now = pygame.time.get_ticks()
        atk_prog = 0.0
        if self.attacking:
            atk_prog = min(1.0, (now - self.attack_start) / max(1, self.attack_duration))

        # ------------------------------------------------------
        # 1. DRAW GOKU SPRITE
        # ------------------------------------------------------

        # scale image to player hitbox height
        # (chỉ scale 1 lần trong __init__, nhưng an toàn thêm guard)
        scale_h = self.rect.height
        if self.goku_img.get_height() != scale_h:
            scale_factor = scale_h / self.goku_base.get_height()
            scale_w = int(self.goku_base.get_width() * scale_factor)
            self.goku_img = pygame.transform.scale(self.goku_base, (scale_w, scale_h))

        # hướng xoay theo facing_right
        if self.facing_right:
            img = self.goku_img
        else:
            img = pygame.transform.flip(self.goku_img, True, False)

        # tilt khi attack cho cảm giác xoay người
        tilt = 0
        if self.attacking:
            tilt = int(6 * atk_prog) if self.facing_right else int(-6 * atk_prog)

        if tilt != 0:
            img = pygame.transform.rotate(img, tilt)

        # blit center theo hitbox
        img_rect = img.get_rect(center=(x, y))
        surf.blit(img, img_rect)

        # ------------------------------------------------------
        # 2. PLACE WEAPON (TAY CỦA GOKU)
        # ------------------------------------------------------
        # Bạn chỉnh offset cho phù hợp với ảnh goku.png của bạn
        # giá trị dưới là mặc định ổn cho đa số sprite
        if self.facing_right:
            hand_offset_x = img_rect.width * 0.25
        else:
            hand_offset_x = -img_rect.width * 0.25

        hand_offset_y = -img_rect.height * 0.05

        hand_pos = (img_rect.centerx + hand_offset_x,
                    img_rect.centery + hand_offset_y)

        # Vẽ weapon
        self.draw_weapon(surf, hand_pos)

        # ------------------------------------------------------
        # 3. MIDNIGHT SLASH EFFECT (GIỮ NGUYÊN CODE CỦA BẠN)
        # ------------------------------------------------------
        if self.attack_type == "midnight" and atk_prog > 0:

            tmp = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
            shoulder = hand_pos  # slash xuất phát từ tay

            import math

            angle_center = 0.0 if self.facing_right else math.pi
            sweep_half = math.radians(60)
            start_angle = angle_center - sweep_half - math.radians(10)
            end_angle = angle_center + sweep_half + math.radians(10)
            current_angle = start_angle + (end_angle - start_angle) * atk_prog

            base_radius = int(70 * self.attack_width_multiplier)
            radius = int(base_radius * (0.6 + 0.6 * atk_prog))
            inner_radius = max(8, int(radius * 0.35))

            steps = 14
            outer_pts = []
            inner_pts = []

            for i in range(steps + 1):
                t = i / steps
                ang = start_angle + (current_angle - start_angle) * t
                px = int(shoulder[0] + math.cos(ang) * radius)
                py = int(shoulder[1] + math.sin(ang) * radius)
                outer_pts.append((px, py))
                ix = int(shoulder[0] + math.cos(ang) * inner_radius)
                iy = int(shoulder[1] + math.sin(ang) * inner_radius)
                inner_pts.append((ix, iy))

            poly = [shoulder] + outer_pts + inner_pts[::-1]

            pygame.draw.polygon(tmp, (160, 60, 200, int(80 * (1 - atk_prog * 0.2))), poly)
            pygame.draw.polygon(tmp, (220, 140, 255, int(120 * atk_prog)), poly)

            # streaks
            for i, p in enumerate(outer_pts[::max(1, len(outer_pts) // 6)]):
                alpha = int(200 * (1 - i / len(outer_pts)))
                pygame.draw.circle(tmp, (255, 220, 255, alpha), p, max(3, int(4 * (1 - i / len(outer_pts)))))

            # sparks
            sparks = 6
            for sidx in range(sparks):
                t = (sidx / sparks + atk_prog * 0.8) % 1.0
                ang = start_angle + (current_angle - start_angle) * t
                sx = int(shoulder[0] + math.cos(ang) * (radius * (0.9 - 0.3 * t)))
                sy = int(shoulder[1] + math.sin(ang) * (radius * (0.9 - 0.3 * t)))
                rad = max(1, int(2 + 2 * (1 - t)))
                col = (255, int(220 * (1 - t)), int(180 * (1 - t)), 220)
                pygame.draw.circle(tmp, col, (sx, sy), rad)

            surf.blit(tmp, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
