"""Layout, tuning, difficulty table, palette and sprites for Beat Cop."""

W, H = 40, 20                  # playfield in cells (1 cell = 2 terminal columns)
FPS = 20
FIELD_TOP = 3                  # terminal row where the playfield starts (rows 0-2 are the HUD)
NEED_COLS, NEED_ROWS = 80, 24
MAX_ARMOR = 100

# playfield rows ----------------------------------------------------------
ROW_BLD_TOP, ROW_BLD_BOT = 2, 6      # skyline
ROW_AWNING = 7
ROW_FACADE = 8
ROW_PED = 9                          # top row of the 3-row pedestrian sprites
ROW_WALK = 12                        # sidewalk slab
ROW_CURB = 13
ROW_ST_TOP, ROW_ST_BOT = 14, 18      # street
ROW_SHOULDER = 19
ROW_CAR = 15                         # top row of the patrol car
CAR_X = 17                           # left cell of the 6-cell patrol car
RET_MIN, RET_MAX = 2, W - 3          # the reticle centre sweeps between these cells

# difficulty --------------------------------------------------------------
# reticle: sweep speed in cells/s (+reticle_step per round)   spawn: seconds between walkers
# civ: share of walkers that are civilians   aim: seconds a thug aims before firing
# aim_delay: seconds a thug walks before he first raises his gun (random in this range)
# damage: armor lost per hit   miss: chance a thug's shot misses   strikes: civilian hits allowed
# quota: thugs to drop in round 1 (+quota_step per round)   armored_round: first round with 2-hit thugs
DIFFS = [
    dict(name="ROOKIE", key="1", reticle=8.0, reticle_step=0.5, spawn=2.4, civ=0.45, aim=1.2,
         aim_delay=(3.0, 6.0), damage=10, miss=0.5, strikes=3, quota=4, quota_step=1,
         armored_round=4, max_peds=4,
         blurb="A SLOW SWEEP, SLOPPY SHOOTERS, THREE STRIKES."),
    dict(name="OFFICER", key="2", reticle=11.0, reticle_step=0.75, spawn=1.9, civ=0.5, aim=0.85,
         aim_delay=(3.0, 5.5), damage=12, miss=0.4, strikes=3, quota=5, quota_step=2,
         armored_round=3, max_peds=5,
         blurb="THE INTENDED BEAT. STAY SHARP."),
    dict(name="DETECTIVE", key="3", reticle=14.0, reticle_step=1.0, spawn=1.5, civ=0.55, aim=0.75,
         aim_delay=(2.5, 4.5), damage=15, miss=0.3, strikes=2, quota=6, quota_step=2,
         armored_round=2, max_peds=6,
         blurb="FAST SWEEP, DEADLY THUGS, TWO STRIKES."),
]

# weapons (upgrade path between rounds) -----------------------------------
# cooldown: seconds between shots   damage: hits per shot   spread: extra cells of tolerance each side
WEAPONS = [
    dict(name="PISTOL", cooldown=0.60, damage=1, spread=0),
    dict(name="REVOLVER", cooldown=0.40, damage=1, spread=0),
    dict(name="MAGNUM", cooldown=0.35, damage=2, spread=0),
    dict(name="RIFLE", cooldown=0.25, damage=2, spread=1),
    dict(name="LASER", cooldown=0.15, damage=3, spread=1),
]
REPAIR_AMOUNT = 50

# scoring
PTS_THUG, PTS_ARMORED, PTS_CLUTCH, PTS_CIVILIAN = 100, 250, 50, 250

# palette (xterm-256 indices; render.py folds these to 8 colours when needed) --
BLACK, WHITE, LTGREY, GREY, DKGREY, DARK = 16, 252, 250, 245, 238, 234
RED, DKRED, ORG, YEL = 196, 124, 214, 226
GRN, CYA, BLU, DKBLU, PUR, MAG, PINK, TAN = 40, 51, 33, 18, 54, 201, 217, 223
BUILDING_COLORS = [DKBLU, PUR, 19, 55, 24]
CIV_COLORS = [GRN, CYA, PINK, BLU, ORG]
LOGO_COLORS = [RED, ORG, YEL, GRN, CYA, BLU, MAG]

# sprites: 3x3 cells. H = head colour, B = body colour, . = see-through -----
SPRITES = {
    "civ": [[".H.", "BBB", "B.B"], [".H.", "BBB", ".B."]],
    "thug": [["HH.", "BBB", "B.B"], ["HH.", "BBB", ".B."]],
    "armored": [["HHH", "BBB", "B.B"], ["HHH", "BBB", ".B."]],
}
DYING = ["X.X", ".X.", "X.X"]
PED_COLORS = {"thug": (GREY, RED), "armored": (MAG, PUR)}

# 3x5 block font for the title logo -----------------------------------------
LOGO_TEXT = "BEAT COP"
LOGO_FONT = {
    "B": ["## ", "# #", "## ", "# #", "## "],
    "E": ["###", "#  ", "## ", "#  ", "###"],
    "A": [" # ", "# #", "###", "# #", "# #"],
    "T": ["###", " # ", " # ", " # ", " # "],
    "C": ["###", "#  ", "#  ", "#  ", "###"],
    "O": ["###", "# #", "# #", "# #", "###"],
    "P": ["###", "# #", "###", "#  ", "#  "],
}
