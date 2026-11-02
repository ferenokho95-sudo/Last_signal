import json
import math
from pathlib import Path
import random
import time
import tkinter as tk
from engine import World, UPGRADES, WIDTH, HEIGHT

BG = '#090f1c'
MINT = '#65f5d1'
SAVE = Path.home() / '.last_signal.json'


class App:
    def __init__(self, root):
        self.root = root
        root.title('Последний сигнал | Space survival')
        root.resizable(False, False)
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg=BG, highlightthickness=0)
        self.canvas.pack()
        self.keys = set()
        self.mouse = (WIDTH/2, HEIGHT/2-100)
        self.firing = False
        self.screen = 'menu'
        self.world = World()
        self.best = self.read_record()
        self.saved = False
        rng = random.Random(12)
        self.stars = [(rng.randrange(WIDTH), rng.randrange(HEIGHT), rng.choice([1, 1, 2])) for _ in range(130)]
        self.last = time.perf_counter()
        root.bind('<KeyPress>', self.press)
        root.bind('<KeyRelease>', lambda e: self.keys.discard(e.keysym.lower()))
        root.bind('<FocusOut>', self.focus_out)
        self.canvas.bind('<Motion>', self.motion)
        self.canvas.bind('<ButtonPress-1>', self.click)
        root.bind('<ButtonRelease-1>', lambda e: setattr(self, 'firing', False))
        root.protocol('WM_DELETE_WINDOW', self.close)
        self.loop()

    def read_record(self):
        try:
            return max(0, int(json.loads(SAVE.read_text()).get('best', 0)))
        except (OSError, ValueError, TypeError, AttributeError):
            return 0

    def save_record(self):
        self.best = max(self.best, self.world.score)
        try:
            SAVE.write_text(json.dumps({'best': self.best}))
        except OSError:
            pass
        self.saved = True

    def close(self):
        self.save_record()
        self.root.destroy()

    def start(self):
        self.world = World()
        self.screen = 'game'
        self.saved = False
        self.keys.clear()
        self.firing = False
        self.canvas.focus_set()

    def focus_out(self, event):
        self.keys.clear()
        self.firing = False
        if self.screen == 'game' and self.world.state == 'playing':
            self.screen = 'pause'

    def motion(self, event):
        self.mouse = (event.x, event.y)

    def press(self, event):
        key = event.keysym.lower()
        fresh = key not in self.keys
        self.keys.add(key)
        if not fresh:
            return
        if key == 'return' and (self.screen == 'menu' or self.world.state == 'over'):
            self.start()
        elif key in ('escape', 'p'):
            if self.screen == 'pause': self.screen = 'game'
            elif self.screen == 'game' and self.world.state == 'playing': self.screen = 'pause'
        elif key in ('1', '2', '3') and self.screen == 'game' and self.world.state == 'upgrade':
            self.world.upgrade(self.world.choices[int(key)-1])

    def click(self, event):
        self.mouse = (event.x, event.y)
        if self.screen == 'menu' or self.world.state == 'over':
            if 390 < event.x < 690 and 440 < event.y < 500:
                self.start()
        elif self.screen == 'game' and self.world.state == 'upgrade':
            for i, key in enumerate(self.world.choices):
                if 100+i*300 < event.x < 380+i*300 and 300 < event.y < 490:
                    self.world.upgrade(key)
                    self.firing = False
                    break
        elif self.screen == 'game':
            self.firing = True

    def text(self, x, y, text, size=14, color='#e4ecff', anchor='center', bold=False):
        self.canvas.create_text(x, y, text=text, fill=color, font=('Arial', size, 'bold' if bold else 'normal'), anchor=anchor)

    def panel(self, x1, y1, x2, y2, outline='#29384f'):
        self.canvas.create_rectangle(x1, y1, x2, y2, fill='#111d30', outline=outline, width=2)

    def loop(self):
        now = time.perf_counter()
        dt = min(.05, now-self.last)
        self.last = now
        if self.screen == 'game':
            k = self.keys
            move = (int('d' in k or 'right' in k)-int('a' in k or 'left' in k),
                    int('s' in k or 'down' in k)-int('w' in k or 'up' in k))
            self.world.update(dt, move, self.mouse, self.firing, 'space' in k)
            if self.world.state == 'over' and not self.saved:
                self.save_record()
        self.draw(now)
        self.root.after(16, self.loop)

    def background(self, now):
        c = self.canvas
        for x in range(0, WIDTH, 60): c.create_line(x, 75, x, HEIGHT, fill='#101a2b')
        for y in range(75, HEIGHT, 60): c.create_line(0, y, WIDTH, y, fill='#101a2b')
        for x, y, r in self.stars:
            yy = (y + now*5*r) % HEIGHT
            c.create_oval(x, yy, x+r, yy+r, fill='#3b5577', outline='')

    def draw(self, now):
        c = self.canvas
        c.delete('all')
        self.background(now)
        if self.screen == 'menu':
            self.text(540, 130, 'ОРБИТАЛЬНЫЙ СЕКТОР  /  07', 12, MINT)
            self.text(540, 230, 'ПОСЛЕДНИЙ СИГНАЛ', 43, bold=True)
            self.text(540, 296, 'Маяк погас. Ты — последний корабль в секторе.', 17, '#9aacc9')
            self.text(540, 330, 'Переживи волны дронов. Собери свой боевой корабль.', 16, '#9aacc9')
            self.panel(390, 440, 690, 500, MINT)
            self.text(540, 470, 'НАЧАТЬ  /  ENTER', 17, MINT, bold=True)
            self.text(540, 545, f'ЛУЧШИЙ СЧЁТ: {self.best}', 14, '#ac91ff')
            self.text(540, 620, 'WASD / стрелки — полёт     ЛКМ — огонь     Пробел — рывок', 14)
            self.text(540, 652, 'P / Esc — пауза    •    Каждый пятый раунд — босс', 12, '#8295b3')
            return
        w, p = self.world, self.world.player
        for item in w.pickups:
            x, y = item.x, item.y
            c.create_oval(x-12, y-12, x+12, y+12, outline=MINT)
            c.create_line(x-6, y, x+6, y, fill=MINT, width=3)
            c.create_line(x, y-6, x, y+6, fill=MINT, width=3)
        for b in w.bullets:
            c.create_line(b.x-b.vx*.012, b.y-b.vy*.012, b.x, b.y, fill=MINT, width=3)
        for b in w.hostile:
            c.create_oval(b.x-5, b.y-5, b.x+5, b.y+5, fill='#ffba73', outline='')
        colors = {'hunter': '#ff6584', 'shooter': '#ffc271', 'tank': '#9d8cff', 'boss': '#e278ff'}
        for e in w.enemies:
            x, y, r = e.x, e.y, e.r
            color = colors[e.kind]
            if e.kind == 'hunter':
                angle = math.atan2(p.y-y, p.x-x)
                pts = []
                for a in (0, 2.4, -2.4): pts += [x+math.cos(angle+a)*r, y+math.sin(angle+a)*r]
                c.create_polygon(*pts, fill='#422238', outline=color, width=2)
            else:
                c.create_polygon(x, y-r, x+r, y, x, y+r, x-r, y, fill='#2c2544', outline=color, width=2)
                c.create_oval(x-4, y-4, x+4, y+4, fill=color, outline='')
            if e.kind == 'boss':
                c.create_rectangle(x-45, y-r-14, x+45, y-r-9, fill='#33233f', outline='')
                c.create_rectangle(x-45, y-r-14, x-45+90*max(0,e.hp)/(230+w.wave*32), y-r-9, fill=color, outline='')
        for b, color in w.particles:
            c.create_oval(b.x-b.r, b.y-b.r, b.x+b.r, b.y+b.r, fill=color, outline='')
        if w.invincible <= 0 or int(now*18)%2 == 0:
            angle = math.atan2(self.mouse[1]-p.y, self.mouse[0]-p.x)
            pts = []
            for a, r in ((0, 22), (2.5, 17), (math.pi, 8), (-2.5, 17)):
                pts += [p.x+math.cos(angle+a)*r, p.y+math.sin(angle+a)*r]
            c.create_polygon(*pts, fill='#153b43', outline=MINT, width=2)
            c.create_oval(p.x-3, p.y-3, p.x+3, p.y+3, fill='white', outline='')
        if self.screen == 'game' and w.state == 'playing':
            x, y = self.mouse
            c.create_oval(x-9, y-9, x+9, y+9, outline='#668b92')
            c.create_line(x-13, y, x+13, y, fill='#668b92')
            c.create_line(x, y-13, x, y+13, fill='#668b92')
        c.create_rectangle(0, 0, WIDTH, 74, fill=BG, outline='')
        c.create_line(0, 74, WIDTH, 74, fill='#2a3b54')
        self.text(25, 22, 'КОРПУС', 10, '#8295b3', 'w')
        c.create_rectangle(25, 40, 245, 51, fill='#293448', outline='')
        c.create_rectangle(25, 40, 25+220*p.hp/w.max_hp, 51, fill=MINT if p.hp>30 else '#ff6584', outline='')
        self.text(258, 45, f'{int(p.hp)} / {w.max_hp}', 11, anchor='w')
        self.text(440, 25, f'ВОЛНА {w.wave:02}', 18, bold=True)
        self.text(440, 51, f'Врагов: {len(w.enemies)+w.remaining}', 11, '#8295b3')
        self.text(650, 26, f'{w.score:06}', 22, MINT, bold=True)
        self.text(650, 53, 'ОЧКИ', 9, '#8295b3')
        self.text(835, 26, 'РЫВОК ГОТОВ' if w.dash_cd <= 0 else f'РЫВОК {w.dash_cd:.1f} c', 12, MINT if w.dash_cd<=0 else '#8295b3')
        self.text(1020, 27, 'P / ПАУЗА', 11, '#8295b3', 'e')
        self.text(1020, 51, f'РЕКОРД {max(self.best,w.score)}', 10, '#ac91ff', 'e')
        if self.screen == 'pause':
            self.panel(300, 260, 780, 450)
            self.text(540, 320, 'ПАУЗА', 30, bold=True)
            self.text(540, 389, 'P или Esc — продолжить', 15, MINT)
        elif w.state == 'upgrade':
            self.panel(65, 170, 1015, 555)
            self.text(540, 217, 'СЕКТОР ЗАЧИЩЕН', 28, MINT, bold=True)
            self.text(540, 260, 'Выбери улучшение корабля — клавиша 1, 2, 3 или щелчок', 14, '#9aacc9')
            for i, key in enumerate(w.choices):
                x = 100+i*300
                hover = x < self.mouse[0] < x+280 and 300 < self.mouse[1] < 490
                self.panel(x, 300, x+280, 490, MINT if hover else '#35465f')
                title, desc = UPGRADES[key]
                self.text(x+25, 332, f'0{i+1}', 13, MINT, 'w')
                self.text(x+140, 387, title, 18, bold=True)
                self.canvas.create_text(x+140, 446, text=desc, width=240, justify='center', fill='#9aacc9', font=('Arial', 12))
        elif w.state == 'over':
            self.panel(280, 205, 800, 545)
            self.text(540, 255, 'СИГНАЛ ПОТЕРЯН', 30, '#ff7791', bold=True)
            self.text(540, 320, f'Счёт: {w.score}    •    Волна: {w.wave}', 20)
            self.text(540, 366, f'Ты продержался {int(w.time)//60:02}:{int(w.time)%60:02}', 14, '#9aacc9')
            self.panel(390, 440, 690, 500, MINT)
            self.text(540, 470, 'ЕЩЁ ПОПЫТКА / ENTER', 14, MINT, bold=True)


if __name__ == '__main__':
    App(tk.Tk()).root.mainloop()
