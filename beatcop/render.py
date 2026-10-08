"""Curses drawing for Beat Cop: fat colour cells, two columns each, 2600 style."""
import curses

from .constants import *  # noqa: F401,F403


def _rgb(c):
    if c < 16:
        return ((c & 1) * 200 + (c > 7) * 55, ((c >> 1) & 1) * 200 + (c > 7) * 55,
                ((c >> 2) & 1) * 200 + (c > 7) * 55)
    if c < 232:
        c -= 16
        lv = [0, 95, 135, 175, 215, 255]
        return lv[c // 36], lv[(c // 6) % 6], lv[c % 6]
    v = 8 + (c - 232) * 10
    return v, v, v


def to8(c):
    """Fold an xterm-256 index down to the 8 basic colours."""
    if c < 16:
        return c & 7
    r, g, b = _rgb(c)
    return (1 if r >= 110 else 0) | (2 if g >= 110 else 0) | (4 if b >= 110 else 0)


def msg_color(text):
    if any(w in text for w in ("HIT!", "CIVILIAN", "GOT AWAY", "REVOKED")):
        return RED
    if any(w in text for w in ("DOWN", "CLUTCH", "MISSED", "REPAIRED", "CARRYING")):
        return GRN
    return YEL


class Renderer:
    def __init__(self, scr):
        self.scr = scr
        self.cache = {}
        self.big = curses.COLORS >= 256
        self.ox = 0
        self.oy = 0
        self.sx = 0                      # screen-shake offset in columns
        self.cols = NEED_COLS
        self.cells = []

    def layout(self, rows, cols):
        self.ox = max(0, (cols - NEED_COLS) // 2)
        self.oy = max(0, (rows - NEED_ROWS) // 2)
        self.cols = cols

    def pair(self, fg, bg):
        key = (fg, bg)
        p = self.cache.get(key)
        if p is None:
            idx = len(self.cache) + 1
            if idx >= curses.COLOR_PAIRS:
                return 0
            f, b = (fg, bg) if self.big else (to8(fg), to8(bg))
            curses.init_pair(idx, f, b)
            p = curses.color_pair(idx)
            self.cache[key] = p
        return p

    # ---- primitives --------------------------------------------------------
    def begin(self):
        self.cells = [[("  ", LTGREY, BLACK)] * W for _ in range(H)]

    def cell(self, y, x, bg, ch="  ", fg=LTGREY):
        if 0 <= y < H and 0 <= x < W:
            self.cells[y][x] = (ch, fg, bg)

    def text(self, row, col, s, fg=LTGREY, bg=BLACK, bold=False):
        col += self.sx
        if col < 0:
            s, col = s[-col:], 0
        s = s[:max(0, self.cols - self.ox - col)]
        if not s:
            return
        attr = self.pair(fg, bg) | (curses.A_BOLD if bold else 0)
        try:
            self.scr.addstr(self.oy + row, self.ox + col, s, attr)
        except curses.error:
            pass

    def centre(self, row, s, fg=LTGREY, bg=BLACK, bold=False):
        self.text(row, (NEED_COLS - len(s)) // 2, s, fg, bg, bold)

    def flush(self):
        for y in range(H):
            row = self.cells[y]
            x = 0
            while x < W:
                _, fg, bg = row[x]
                j = x
                buf = ""
                while j < W and row[j][1] == fg and row[j][2] == bg:
                    buf += row[j][0]
                    j += 1
                self.text(FIELD_TOP + y, x * 2, buf, fg, bg)
                x = j

    def box(self, top, gx0, gx1, lines, fg=WHITE):
        """A solid black panel over playfield cells gx0..gx1 with a chunky border.
        Each line is a string or a (string, colour) tuple."""
        width = (gx1 - gx0 + 1) * 2
        self.text(FIELD_TOP + top - 1, gx0 * 2, "▄" * width, GREY, BLACK)
        for i, ln in enumerate(lines):
            col = fg
            if isinstance(ln, tuple):
                ln, col = ln
            self.text(FIELD_TOP + top + i, gx0 * 2, ln.center(width)[:width], col, BLACK, True)
        self.text(FIELD_TOP + top + len(lines), gx0 * 2, "▀" * width, GREY, BLACK)

    def sprite(self, y, x, frame, head, body, facing=1):
        for r, line in enumerate(frame):
            if facing < 0:
                line = line[::-1]
            for c, ch in enumerate(line):
                if ch == "H":
                    self.cell(y + r, x + c, head)
                elif ch in "BX":
                    self.cell(y + r, x + c, body)

    # ---- the street ----------------------------------------------------------
    def draw_world(self, g):
        for (y, x) in g.stars:
            if (g.frame // 7 + x) % 9:
                self.cell(y, x, BLACK, ". ", GREY)
        self.cell(0, 35, YEL)
        self.cell(0, 36, YEL)
        for (x, w, h, col, wins) in g.buildings:
            for y in range(ROW_BLD_BOT - h + 1, ROW_BLD_BOT + 1):
                for cx in range(x, x + w):
                    self.cell(y, cx, col)
            for (wx, wy) in wins:
                if (wx * 7 + wy * 13 + g.frame // 25) % 11:
                    self.cell(ROW_BLD_BOT - wy, wx, YEL if (wx + wy) % 3 else ORG)
        for x in range(W):
            self.cell(ROW_AWNING, x, RED if x % 2 == 0 else WHITE)
            self.cell(ROW_FACADE, x, DARK)
            self.cell(ROW_WALK, x, GREY)
            self.cell(ROW_CURB, x, LTGREY)
            for y in range(ROW_ST_TOP, ROW_ST_BOT + 1):
                self.cell(y, x, DKGREY)
            self.cell(ROW_SHOULDER, x, DARK)
        for x in range(3, W, 9):                       # lit doorways
            self.cell(ROW_FACADE, x, ORG)
        for x in range(1, W, 6):                       # lane dashes
            self.cell(ROW_ST_TOP + 2, x, YEL)
            self.cell(ROW_ST_TOP + 2, x + 1, YEL)

    def draw_ped(self, g, p):
        x = int(round(p.x))
        if p.state == "dying":
            self.sprite(ROW_PED, x, DYING, WHITE, WHITE)
            return
        fi = int(p.anim * 5) % 2 if p.state in ("walk", "flee") else 0
        body = p.body
        if p.state == "aim":
            body = YEL if (g.frame // 3) % 2 else RED
        self.sprite(ROW_PED, x, SPRITES[p.kind][fi], p.head, body, p.d)
        if p.state == "aim":
            self.cell(ROW_PED + 1, x + 3 if p.d > 0 else x - 1, body)       # the gun arm
            if (g.frame // 4) % 2:
                self.cell(ROW_FACADE, x + 1, DARK, "! ", YEL)

    def draw_reticle(self, g):
        rx = int(round(g.rx))
        col = YEL if g.cooldown <= 0 else DKRED
        for dx in (-2, -1, 1, 2):
            self.cell(ROW_FACADE, rx + dx, col)
            self.cell(ROW_WALK, rx + dx, col)
        for r in (ROW_PED, ROW_PED + 2):
            self.cell(r, rx - 2, col)
            self.cell(r, rx + 2, col)

    def draw_car(self, g):
        lb = (g.frame // 5) % 2
        self.cell(ROW_CAR, CAR_X + 2, RED if lb else BLU)
        self.cell(ROW_CAR, CAR_X + 3, BLU if lb else RED)
        for c in range(6):
            self.cell(ROW_CAR + 1, CAR_X + c, WHITE)
        self.cell(ROW_CAR + 1, CAR_X + 2, CYA)
        self.cell(ROW_CAR + 1, CAR_X + 3, CYA)
        self.cell(ROW_CAR + 2, CAR_X + 1, DARK)
        self.cell(ROW_CAR + 2, CAR_X + 2, WHITE)
        self.cell(ROW_CAR + 2, CAR_X + 3, WHITE)
        self.cell(ROW_CAR + 2, CAR_X + 4, DARK)

    def draw_hud(self, g, sound):
        d = g.d
        self.text(0, 0, " " * NEED_COLS)
        self.text(1, 0, " " * NEED_COLS)
        self.text(2, 0, " " * NEED_COLS)
        self.text(0, 1, "SCORE", LTGREY)
        self.text(0, 7, "%06d" % min(g.score, 999999), YEL, BLACK, True)
        self.text(0, 18, "HI", LTGREY)
        self.text(0, 21, "%06d" % g.best, WHITE, BLACK, True)
        self.text(0, 32, "ROUND %02d" % g.round, WHITE, BLACK, True)
        self.text(0, 44, d["name"], CYA, BLACK, True)
        blocks = int(round(g.armor / 10.0))
        acol = GRN if g.armor > 50 else (YEL if g.armor > 25 else RED)
        self.text(1, 1, "ARMOR", LTGREY)
        self.text(1, 7, "█" * blocks + "░" * (10 - blocks), acol, BLACK, True)
        self.text(1, 18, "%3d" % g.armor, acol, BLACK, True)
        w = WEAPONS[g.weapon]
        self.text(1, 24, "WEAPON", LTGREY)
        self.text(1, 31, "%-8s" % w["name"], WHITE, BLACK, True)
        self.text(1, 40, "▮" * (g.weapon + 1) + "▯" * (len(WEAPONS) - g.weapon - 1), CYA, BLACK, True)
        self.text(1, 48, "STRIKES", LTGREY)
        self.text(1, 56, " ".join(["X"] * g.strikes + ["_"] * (d["strikes"] - g.strikes)), RED, BLACK, True)
        self.text(1, 64, "THUGS LEFT", LTGREY)
        self.text(1, 75, "%2d" % max(0, g.quota - g.kills), RED, BLACK, True)
        text, t = g.msg
        if t > 0 and text:
            self.centre(2, text, msg_color(text), BLACK, True)
        hint = " SPACE FIRE    P PAUSE    M SOUND %s    Q QUIT " % ("ON " if sound else "OFF")
        self.centre(NEED_ROWS - 1, hint, GREY)

    def draw(self, g, sound):
        self.sx = (1 if g.frame % 2 else -1) if g.shake > 0 else 0
        self.begin()
        self.draw_world(g)
        for p in g.peds:
            self.draw_ped(g, p)
        if g.tracer > 0:
            for r in range(ROW_PED, ROW_CAR):
                self.cell(r, g.tracer_x, WHITE)
        if g.eshot > 0:
            for r in range(ROW_WALK, ROW_CAR + 1):
                self.cell(r, g.eshot_x, RED)
        self.draw_reticle(g)
        self.draw_car(g)
        self.flush()
        for text, x, t in g.floats:
            row = ROW_FACADE - int((0.9 - t) / 0.3)
            self.text(FIELD_TOP + row, x * 2 - len(text) // 2, text, YEL, BLACK, True)
        self.draw_hud(g, sound)
        if g.phase == "shop":
            self.shop_overlay(g)

    # ---- overlays --------------------------------------------------------------
    def shop_overlay(self, g):
        w = WEAPONS[g.weapon]
        lines = [
            "",
            ("ROUND %d CLEAR" % g.round, YEL),
            "",
            "SCORE %06d    ARMOR %3d/%d    WEAPON %s" % (g.score, g.armor, MAX_ARMOR, w["name"]),
            "",
            ("CHOOSE ONE", WHITE),
            "",
            ("1   REPAIR ARMOR     +%d ARMOR%s" % (REPAIR_AMOUNT, "  (ALREADY FULL)" if g.armor >= MAX_ARMOR else ""), GRN),
            "",
        ]
        if g.can_upgrade():
            nxt = WEAPONS[g.weapon + 1]
            lines.append(("2   UPGRADE WEAPON   %s -> %s" % (w["name"], nxt["name"]), CYA))
            lines.append(("    DAMAGE %d   RELOAD %.2fS   SPREAD %s" % (nxt["damage"], nxt["cooldown"],
                          "WIDE" if nxt["spread"] else "TIGHT"), CYA))
        else:
            lines.append(("2   UPGRADE WEAPON   (MAXED OUT)", GREY))
            lines.append("")
        lines.append("")
        lines.append(("PRESS 1 OR 2" if (g.frame // 8) % 2 else "", YEL))
        self.box(3, 5, 34, lines)

    def pause_overlay(self):
        self.box(8, 11, 28, ["", "P A U S E D", "", "P  RESUME     Q  QUIT TO TITLE", ""])


def end_overlay(ui, g, best, new_best):
    lines = [
        "",
        ("G A M E   O V E R", RED),
        "",
        g.result,
        "",
        "SCORE %06d    ROUND %d    THUGS DOWN %d" % (g.score, g.round, g.total_kills),
        "%s BEST %06d" % (g.d["name"], best),
        "",
        ("*  NEW HIGH SCORE  *" if new_best and (g.frame // 6) % 2 else "", YEL),
        "",
        ("SPACE  TITLE SCREEN        Q  QUIT", WHITE),
        "",
    ]
    ui.box(4, 5, 34, lines)


def title_screen(ui, frame, sel, scores, sound):
    ui.sx = 0
    ui.begin()
    for (y, x) in ((0, 3), (0, 11), (1, 20), (0, 27), (1, 33), (0, 38), (1, 7), (6, 36), (6, 2)):
        if (frame // 9 + x) % 7:
            ui.cell(y, x, BLACK, ". ", GREY)
    x0 = (W - len(LOGO_TEXT) * 4 + 1) // 2
    for i, ch in enumerate(LOGO_TEXT):
        if ch == " ":
            continue
        col = LOGO_COLORS[(i + frame // 4) % len(LOGO_COLORS)]
        for r, line in enumerate(LOGO_FONT[ch]):
            for c, px in enumerate(line):
                if px == "#":
                    ui.cell(1 + r, x0 + i * 4 + c, col)
    walk = SPRITES
    fi = (frame // 4) % 2
    ui.sprite(13, 4, walk["thug"][fi], PED_COLORS["thug"][0], PED_COLORS["thug"][1])
    ui.sprite(13, 17, walk["armored"][fi], PED_COLORS["armored"][0], PED_COLORS["armored"][1])
    ui.sprite(13, 27, walk["civ"][fi], TAN, GRN)
    ui.flush()
    for row in range(3):
        ui.text(row, 0, " " * NEED_COLS)
    ui.centre(1, "A CITY PATROL SHOOTER, 1982 STYLE", GREY)
    ui.centre(FIELD_TOP + 7, "SELECT DIFFICULTY    (UP / DOWN, THEN SPACE)", WHITE, BLACK, True)
    for i, d in enumerate(DIFFS):
        line = "%s  %s  %-9s   HI %06d" % (">" if i == sel else " ", d["key"], d["name"], scores.get(d["name"], 0))
        ui.centre(FIELD_TOP + 8 + i, line, YEL if i == sel else LTGREY, BLACK, i == sel)
    ui.centre(FIELD_TOP + 11, DIFFS[sel]["blurb"], GREY)
    ui.text(FIELD_TOP + 14, 16, "THUG - SHOOT", RED, BLACK, True)
    ui.text(FIELD_TOP + 14, 42, "ARMORED - 2 HITS", MAG, BLACK, True)
    ui.text(FIELD_TOP + 14, 62, "CIVILIAN - SPARE", GRN, BLACK, True)
    ui.centre(FIELD_TOP + 17, "THE RETICLE SWEEPS BY ITSELF. PRESS SPACE WHEN IT CROSSES A THUG.", LTGREY)
    ui.centre(FIELD_TOP + 18, "A THUG WHO RAISES HIS GUN (!) SHOOTS YOUR ARMOR. HIT A CIVILIAN, TAKE A STRIKE.", LTGREY)
    if (frame // 8) % 2:
        ui.centre(FIELD_TOP + 19, "PRESS SPACE TO START", YEL, BLACK, True)
    ui.centre(NEED_ROWS - 1, " Q QUIT    M SOUND %s " % ("ON " if sound else "OFF"), GREY)
