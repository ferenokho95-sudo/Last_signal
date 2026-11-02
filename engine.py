"""Правила боя. Не зависят от графического интерфейса."""
from dataclasses import dataclass
import math
import random

WIDTH, HEIGHT = 1080, 720


def unit(x, y):
    length = math.hypot(x, y)
    return (x / length, y / length) if length else (0, -1)


@dataclass
class Body:
    x: float
    y: float
    vx: float = 0
    vy: float = 0
    r: float = 8
    hp: float = 1
    kind: str = ''
    timer: float = 0
    life: float = 3


UPGRADES = {
    'damage': ('УСИЛИТЕЛЬ', '+35% к урону каждого выстрела'),
    'speed': ('ИМПУЛЬС', 'Стрельба на 20% быстрее'),
    'spread': ('СПЕКТР', '+1 снаряд за выстрел, максимум 5'),
    'hull': ('КОРПУС', '+30 к максимуму и текущему здоровью'),
    'engine': ('ФОРСАЖ', '+12% к скорости корабля'),
    'repair': ('РЕМКОМПЛЕКТ', 'Полное восстановление здоровья'),
}


class World:
    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.player = Body(WIDTH / 2, HEIGHT / 2, r=14, hp=100)
        self.max_hp = 100
        self.damage = 12
        self.interval = .19
        self.speed = 245
        self.pellets = 1
        self.cooldown = 0
        self.dash_cd = 0
        self.dash_time = 0
        self.invincible = 0
        self.time = 0
        self.score = 0
        self.wave = 0
        self.enemies = []
        self.bullets = []
        self.hostile = []
        self.particles = []
        self.pickups = []
        self.remaining = 0
        self.spawn_cd = 0
        self.state = 'playing'
        self.choices = []
        self.begin_wave()

    def begin_wave(self):
        self.wave += 1
        self.remaining = 5 + self.wave * 3
        self.spawn_cd = .5
        self.hostile.clear()
        self.bullets.clear()
        self.state = 'playing'
        self.invincible = 1.2
        if self.wave % 5 == 0:
            self.enemies.append(Body(WIDTH/2, 100, r=42, hp=230+self.wave*32, kind='boss', timer=1.4))

    def upgrade(self, key):
        if self.state != 'upgrade' or key not in self.choices:
            return
        if key == 'damage': self.damage *= 1.35
        elif key == 'speed': self.interval = max(.065, self.interval * .8)
        elif key == 'spread': self.pellets = min(5, self.pellets + 1)
        elif key == 'hull':
            self.max_hp += 30
            self.player.hp = min(self.max_hp, self.player.hp + 30)
        elif key == 'engine': self.speed *= 1.12
        elif key == 'repair': self.player.hp = self.max_hp
        self.begin_wave()

    def burst(self, x, y, color, count=12):
        for _ in range(count):
            angle = self.rng.random() * math.tau
            speed = self.rng.uniform(30, 170)
            self.particles.append((Body(x, y, math.cos(angle)*speed, math.sin(angle)*speed,
                                        r=self.rng.uniform(1, 3), life=self.rng.uniform(.2, .6)), color))

    def hit_player(self, amount):
        if self.invincible > 0 or self.state != 'playing':
            return
        self.player.hp -= amount
        self.invincible = .65
        self.burst(self.player.x, self.player.y, '#ff6e91')
        if self.player.hp <= 0:
            self.player.hp = 0
            self.state = 'over'

    def spawn(self):
        edge = self.rng.randrange(4)
        x, y = [(20, self.rng.uniform(85, HEIGHT-20)),
                (WIDTH-20, self.rng.uniform(85, HEIGHT-20)),
                (self.rng.uniform(20, WIDTH-20), 85),
                (self.rng.uniform(20, WIDTH-20), HEIGHT-20)][edge]
        kind = self.rng.choices(['hunter', 'shooter', 'tank'], [6, 2 if self.wave >= 2 else 0, 2 if self.wave >= 3 else 0])[0]
        hp, radius = {'hunter': (22, 12), 'shooter': (28, 15), 'tank': (65, 22)}[kind]
        self.enemies.append(Body(x, y, r=radius, hp=hp*(1+self.wave*.09), kind=kind, timer=1))

    def update(self, dt, move=(0, 0), aim=None, firing=False, dash=False):
        if self.state != 'playing':
            return
        dt = min(dt, .05)
        self.time += dt
        for attr in ('cooldown', 'dash_cd', 'dash_time', 'invincible'):
            setattr(self, attr, max(0, getattr(self, attr)-dt))
        p = self.player
        mx, my = move
        dx, dy = unit(mx, my) if mx or my else (0, 0)
        if dash and self.dash_cd <= 0 and (mx or my):
            self.dash_time = .15
            self.dash_cd = 2.4
            self.invincible = max(self.invincible, .22)
            self.burst(p.x, p.y, '#64f4df', 16)
        speed = self.speed * (4 if self.dash_time > 0 else 1)
        p.x = max(18, min(WIDTH-18, p.x + dx*speed*dt))
        p.y = max(90, min(HEIGHT-18, p.y + dy*speed*dt))
        if firing and aim and self.cooldown <= 0:
            angle = math.atan2(aim[1]-p.y, aim[0]-p.x)
            for i in range(self.pellets):
                a = angle + (i-(self.pellets-1)/2)*.14
                self.bullets.append(Body(p.x, p.y, math.cos(a)*680, math.sin(a)*680, r=4, hp=self.damage, life=1.8))
            self.cooldown = self.interval
        self.spawn_cd -= dt
        if self.remaining and self.spawn_cd <= 0:
            self.spawn()
            self.remaining -= 1
            self.spawn_cd = max(.24, .95-self.wave*.035)
        for enemy in self.enemies:
            ex, ey = unit(p.x-enemy.x, p.y-enemy.y)
            dist = math.hypot(p.x-enemy.x, p.y-enemy.y)
            speed = {'hunter': 82+self.wave*3, 'tank': 48+self.wave*2, 'shooter': 65, 'boss': 40}[enemy.kind]
            if enemy.kind in ('shooter', 'boss') and dist < 270:
                speed = -25 if dist < 190 else 0
            enemy.x = max(enemy.r, min(WIDTH-enemy.r, enemy.x+ex*speed*dt))
            enemy.y = max(85+enemy.r, min(HEIGHT-enemy.r, enemy.y+ey*speed*dt))
            enemy.timer -= dt
            if enemy.kind in ('shooter', 'boss') and enemy.timer <= 0:
                angle = math.atan2(ey, ex)
                angles = [angle] if enemy.kind == 'shooter' else [angle + i*math.tau/12 for i in range(12)]
                for a in angles:
                    self.hostile.append(Body(enemy.x, enemy.y, math.cos(a)*210, math.sin(a)*210, r=6, life=6))
                enemy.timer = 1.7 if enemy.kind == 'shooter' else 1.4
            if dist < p.r+enemy.r:
                self.hit_player(22 if enemy.kind == 'tank' else 14)
        for bullet in self.bullets:
            bullet.x += bullet.vx*dt
            bullet.y += bullet.vy*dt
            bullet.life -= dt
            for enemy in self.enemies:
                if enemy.hp > 0 and math.hypot(bullet.x-enemy.x, bullet.y-enemy.y) < bullet.r+enemy.r:
                    enemy.hp -= bullet.hp
                    bullet.life = 0
                    self.burst(bullet.x, bullet.y, '#ffda89', 3)
                    break
        for enemy in self.enemies[:]:
            if enemy.hp <= 0:
                self.enemies.remove(enemy)
                self.score += 500 if enemy.kind == 'boss' else 30 if enemy.kind == 'tank' else 10
                self.burst(enemy.x, enemy.y, '#bb8cff' if enemy.kind == 'boss' else '#ff7791', 22)
                if self.rng.random() < .15 or enemy.kind == 'boss':
                    self.pickups.append(Body(enemy.x, enemy.y, r=9, life=12))
        for bullet in self.hostile:
            bullet.x += bullet.vx*dt
            bullet.y += bullet.vy*dt
            bullet.life -= dt
            if math.hypot(bullet.x-p.x, bullet.y-p.y) < bullet.r+p.r:
                self.hit_player(12)
                bullet.life = 0
        self.bullets = [b for b in self.bullets if b.life > 0 and -20 < b.x < WIDTH+20 and 70 < b.y < HEIGHT+20]
        self.hostile = [b for b in self.hostile if b.life > 0 and -20 < b.x < WIDTH+20 and 70 < b.y < HEIGHT+20]
        for pickup in self.pickups[:]:
            pickup.life -= dt
            if math.hypot(pickup.x-p.x, pickup.y-p.y) < pickup.r+p.r+5:
                p.hp = min(self.max_hp, p.hp+20)
                self.pickups.remove(pickup)
                self.burst(p.x, p.y, '#64f4df')
            elif pickup.life <= 0:
                self.pickups.remove(pickup)
        for particle, _ in self.particles:
            particle.x += particle.vx*dt
            particle.y += particle.vy*dt
            particle.life -= dt
        self.particles = [(b, c) for b, c in self.particles if b.life > 0][-450:]
        if self.state == 'playing' and self.remaining == 0 and not self.enemies:
            self.state = 'upgrade'
            available = [k for k in UPGRADES if k != 'spread' or self.pellets < 5]
            self.choices = self.rng.sample(available, 3)
            self.hostile.clear()
