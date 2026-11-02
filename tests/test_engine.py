import unittest
from engine import World, Body, WIDTH, HEIGHT


class BattleTests(unittest.TestCase):
    def test_diagonal_speed(self):
        a, b = World(1), World(1)
        a.update(.05, (1, 0))
        b.update(.05, (1, 1))
        self.assertAlmostEqual(a.player.x-WIDTH/2, ((b.player.x-WIDTH/2)**2+(b.player.y-HEIGHT/2)**2)**.5)

    def test_shot_and_wave_completion(self):
        w = World(12)
        w.remaining = 0
        w.enemies = [Body(w.player.x+20, w.player.y, hp=10, kind='hunter')]
        w.update(.02, aim=(1000, w.player.y), firing=True)
        self.assertEqual(w.score, 10)
        self.assertEqual(w.state, 'upgrade')
        self.assertEqual(len(w.choices), 3)

    def test_dash(self):
        w = World(12)
        w.invincible = 0
        w.update(.02, (1, 0), dash=True)
        old = w.player.hp
        w.hit_player(20)
        self.assertEqual(w.player.hp, old)
        self.assertGreater(w.dash_cd, 2)

    def test_upgrade(self):
        w = World(1)
        w.remaining = 0
        w.update(.01)
        self.assertEqual(w.state, 'upgrade')
        w.upgrade(w.choices[0])
        self.assertEqual((w.wave, w.state), (2, 'playing'))

    def test_boss(self):
        w = World(1)
        w.wave = 4
        w.begin_wave()
        self.assertTrue(any(e.kind == 'boss' for e in w.enemies))

    def test_death(self):
        w = World(1)
        w.invincible = 0
        w.hit_player(200)
        old = w.time
        w.update(.05)
        self.assertEqual(w.state, 'over')
        self.assertEqual(w.time, old)

    def test_bounds(self):
        w = World(1)
        w.player.x, w.player.y = WIDTH-1, HEIGHT-1
        w.update(.05, (1, 1), dash=True)
        self.assertLessEqual(w.player.x, WIDTH-18)
        self.assertLessEqual(w.player.y, HEIGHT-18)

    def test_projectiles_expire(self):
        w = World(1)
        w.bullets = [Body(100, 100, life=.01)]
        w.hostile = [Body(100, 100, life=.01)]
        w.update(.02)
        self.assertFalse(w.bullets)
        self.assertFalse(w.hostile)

    def test_simulation(self):
        w = World(42)
        for _ in range(12000):
            if w.state == 'over': break
            if w.state == 'upgrade': w.upgrade(w.choices[0])
            w.update(1/60, (1 if int(w.time)%4<2 else -1, 0), (400, 200), True, True)
            self.assertLessEqual(len(w.particles), 450)
            self.assertGreaterEqual(w.player.hp, 0)
        self.assertGreater(w.time, 1)


if __name__ == '__main__':
    unittest.main()
