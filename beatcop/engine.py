"""Game rules for Beat Cop. No curses in here, so it runs headless for testing."""
import json
import os
import random

from .constants import *  # noqa: F401,F403

SCORE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "highscore.json")


def load_scores():
    try:
        with open(SCORE_PATH) as f:
            data = json.load(f)
        return {str(k): int(v) for k, v in data.items()}
    except (OSError, ValueError, TypeError, AttributeError):
        return {}


def save_scores(scores):
    try:
        with open(SCORE_PATH, "w") as f:
            json.dump(scores, f, indent=2)
    except OSError:
        pass


class Ped:
    """A walker on the sidewalk: a civilian, a thug or an armored thug."""

    def __init__(self, kind, x, d, speed, hp, head, body, rng):
        self.kind = kind          # "civ", "thug" or "armored"
        self.x = float(x)         # left cell of the 3-cell sprite
        self.d = d                # +1 walking right, -1 walking left
        self.speed = speed        # cells per second
        self.hp = hp
        self.head = head
        self.body = body
        self.state = "walk"       # walk, aim, flee or dying
        self.t = 0.0              # timer for the current state
        self.anim = rng.random() * 2
        self.next_aim = 0.0       # set by Game.spawn from the difficulty's aim_delay

    @property
    def cx(self):
        return self.x + 1.0

    @property
    def hostile(self):
        return self.kind != "civ"


class Game:
    def __init__(self, diff_index, seed=None):
        self.rng = random.Random(seed)
        self.d = DIFFS[diff_index]
        self.frame = 0
        self.time = 0.0
        self.score = 0
        self.round = 1
        self.armor = MAX_ARMOR
        self.strikes = 0
        self.weapon = 0
        self.total_kills = 0
        self.result = None        # set to a reason string when the game ends
        self.beep = False         # True for one frame when the terminal should click
        self.msg = ("", 0.0)
        self.floats = []          # [text, cell x, seconds left]
        self.buildings = []
        self.stars = []
        self.new_skyline()
        self.start_round()

    # ---- setup -----------------------------------------------------------
    def say(self, text, secs=1.6):
        self.msg = (text, secs)

    def new_skyline(self):
        r = self.rng
        self.buildings = []
        x = 0
        while x < W:
            w = r.randint(3, 6)
            w = min(w, W - x)
            h = r.randint(1, ROW_BLD_BOT - ROW_BLD_TOP + 1)
            col = r.choice(BUILDING_COLORS)
            wins = [(wx, wy) for wx in range(x, x + w) for wy in range(h)
                    if (wx - x) % 2 == 0 and r.random() < 0.55]
            self.buildings.append((x, w, h, col, wins))
            x += w + r.randint(0, 1)
        self.stars = [(r.randint(0, 1), r.randint(0, W - 1)) for _ in range(10)]

    def start_round(self):
        d = self.d
        self.peds = []
        self.floats = []
        self.kills = 0
        self.escaped = 0
        self.quota = d["quota"] + d["quota_step"] * (self.round - 1)
        self.rx = float(RET_MIN)
        self.rdir = 1
        self.rspeed = d["reticle"] + d["reticle_step"] * (self.round - 1)
        self.cooldown = 0.0
        self.spawn_t = 0.8
        self.tracer = 0.0
        self.tracer_x = 0
        self.eshot = 0.0
        self.eshot_x = 0
        self.shake = 0.0
        self.phase = "intro"      # intro, play, clear or shop
        self.phase_t = 1.5
        self.say("ROUND %d  -  PATROL!" % self.round, 1.8)

    # ---- per frame -------------------------------------------------------
    def step(self, keys):
        dt = 1.0 / FPS
        self.frame += 1
        self.time += dt
        self.beep = False
        text, t = self.msg
        if t > 0:
            self.msg = (text, t - dt)
        self.cooldown = max(0.0, self.cooldown - dt)
        self.tracer = max(0.0, self.tracer - dt)
        self.eshot = max(0.0, self.eshot - dt)
        self.shake = max(0.0, self.shake - dt)
        for f in self.floats:
            f[2] -= dt
        self.floats = [f for f in self.floats if f[2] > 0]
        if self.result:
            return
        if self.phase == "shop":
            self.shop_keys(keys)
            return

        # the reticle sweeps on its own
        self.rx += self.rdir * self.rspeed * dt
        if self.rx >= RET_MAX:
            self.rx, self.rdir = float(RET_MAX), -1
        elif self.rx <= RET_MIN:
            self.rx, self.rdir = float(RET_MIN), 1
        if "btn" in keys and self.cooldown <= 0:
            self.fire()

        if self.phase == "intro":
            self.phase_t -= dt
            if self.phase_t <= 0:
                self.phase = "play"
        elif self.phase == "play":
            self.spawn_t -= dt
            if self.spawn_t <= 0:
                if len(self.peds) < self.d["max_peds"]:
                    self.spawn()
                self.spawn_t = self.d["spawn"] * self.rng.uniform(0.7, 1.3)
        elif self.phase == "clear":
            self.phase_t -= dt
            if self.phase_t <= 0:
                self.phase = "shop"

        self.step_peds(dt)

        if self.phase == "play" and self.kills >= self.quota:
            self.phase = "clear"
            self.phase_t = 1.6
            self.say("ROUND %d CLEAR!" % self.round, 1.6)
            for p in self.peds:
                if p.state == "aim":
                    p.state = "flee"

    def step_peds(self, dt):
        d = self.d
        for p in self.peds:
            p.anim += dt
            if p.state == "walk":
                p.x += p.d * p.speed * dt
                if p.hostile and self.phase == "play":
                    p.next_aim -= dt
                    if p.next_aim <= 0 and 3 <= p.x <= W - 6:
                        p.state = "aim"
                        p.t = d["aim"]
                        self.beep = True
            elif p.state == "aim":
                p.t -= dt
                if p.t <= 0:
                    self.enemy_fires(p)
            elif p.state == "flee":
                p.x += p.d * p.speed * 2.2 * dt
            elif p.state == "dying":
                p.t -= dt
        keep = []
        for p in self.peds:
            if p.state == "dying" and p.t <= 0:
                continue
            if p.x < -3 or p.x > W:
                if p.hostile and p.state != "dying" and self.phase == "play":
                    self.escaped += 1
                    self.say("A THUG GOT AWAY")
                continue
            keep.append(p)
        self.peds = keep

    def spawn(self):
        d, r = self.d, self.rng
        side = r.choice((1, -1))
        x = -3.0 if side == 1 else float(W)
        for q in self.peds:
            if abs(q.x - x) < 4:
                return                      # somebody is already in the doorway
        speed = r.uniform(2.0, 4.0) + 0.15 * (self.round - 1)
        if r.random() < d["civ"]:
            self.peds.append(Ped("civ", x, side, speed, 1, TAN, r.choice(CIV_COLORS), r))
            return
        armored = False
        if self.round >= d["armored_round"]:
            armored = r.random() < min(0.6, 0.3 + 0.1 * (self.round - d["armored_round"]))
        kind = "armored" if armored else "thug"
        head, body = PED_COLORS[kind]
        p = Ped(kind, x, side, speed * 0.85, 2 if armored else 1, head, body, r)
        p.next_aim = r.uniform(*d["aim_delay"])
        self.peds.append(p)

    # ---- shooting --------------------------------------------------------
    def fire(self):
        w = WEAPONS[self.weapon]
        self.cooldown = w["cooldown"]
        rx = int(round(self.rx))
        self.tracer = 0.12
        self.tracer_x = rx
        # A thug under the reticle always takes the bullet; a civilian is only hit
        # when nobody hostile is in the window, so overlapping walkers are not a trap.
        best = None
        for p in self.peds:
            if p.state == "dying":
                continue
            if p.x - w["spread"] <= rx <= p.x + 2 + w["spread"]:
                rank = (0 if p.hostile else 1, abs(p.cx - rx))
                if best is None or rank < best[0]:
                    best = (rank, p)
        if best is None:
            return
        p = best[1]
        self.beep = True
        if not p.hostile:
            p.state, p.t = "dying", 0.3
            self.strikes += 1
            self.score = max(0, self.score - PTS_CIVILIAN)
            self.add_float("-%d" % PTS_CIVILIAN, p.cx)
            self.shake = 0.3
            if self.strikes >= self.d["strikes"]:
                self.say("CIVILIAN HIT!  BADGE REVOKED")
                self.result = "BADGE REVOKED: TOO MANY CIVILIANS HIT"
            else:
                self.say("CIVILIAN HIT!  STRIKE %d OF %d" % (self.strikes, self.d["strikes"]))
            return
        p.hp -= w["damage"]
        if p.hp > 0:
            self.add_float("CLANG", p.cx)
            self.say("ARMORED!  HIT HIM AGAIN")
            p.next_aim = min(p.next_aim, 0.4)      # that made him angry
            return
        pts = PTS_ARMORED if p.kind == "armored" else PTS_THUG
        if p.state == "aim":
            pts += PTS_CLUTCH
            self.say("CLUTCH SHOT!  +%d" % pts)
        else:
            self.say("THUG DOWN  +%d" % pts)
        p.state, p.t = "dying", 0.3
        self.score += pts
        self.kills += 1
        self.total_kills += 1
        self.add_float("+%d" % pts, p.cx)

    def enemy_fires(self, p):
        p.state = "flee"
        hit = self.rng.random() >= self.d["miss"]
        self.eshot = 0.2
        self.eshot_x = int(round(p.cx)) + (0 if hit else self.rng.choice((-3, 3)))
        self.beep = True
        if hit:
            self.armor -= self.d["damage"]
            self.shake = 0.25
            self.say("HIT!  ARMOR -%d" % self.d["damage"])
            if self.armor <= 0:
                self.armor = 0
                self.result = "ARMOR DESTROYED"
        else:
            self.say("THE THUG MISSED!")

    def add_float(self, text, cx):
        self.floats.append([text, int(round(cx)), 0.9])

    # ---- between rounds --------------------------------------------------
    def can_upgrade(self):
        return self.weapon < len(WEAPONS) - 1

    def shop_keys(self, keys):
        for k in keys:
            if k in ("1", "r"):
                self.armor = min(MAX_ARMOR, self.armor + REPAIR_AMOUNT)
                self.next_round("ARMOR REPAIRED")
                return
            if k in ("2", "u", "w") and self.can_upgrade():
                self.weapon += 1
                self.next_round("NOW CARRYING THE %s" % WEAPONS[self.weapon]["name"])
                return

    def next_round(self, note):
        self.round += 1
        self.new_skyline()
        self.start_round()
        self.say("%s  -  ROUND %d" % (note, self.round), 2.0)
