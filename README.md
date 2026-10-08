# Beat Cop

Night shift in a city that has given up. Your patrol car idles at the curb
while thugs and civilians share the sidewalk in front of you. Your targeting
reticle sweeps left and right on its own, so the whole game is timing: press
the button the instant it crosses a thug, and never when it crosses a civilian.
A thug who stops and raises his gun will shoot your armor unless you drop him
first. Between rounds you choose one thing: repair your armor or improve your
weapon. Atari 2600 looks, one screen, one button, inside your terminal.

```bash
./play.sh [rookie|officer|detective] [--sound]
```

or `python3 -m beatcop` from this folder. Needs Python 3 (ships with macOS)
and a terminal at least 80 columns by 24 rows. A 256-colour terminal gives the
full palette; 8-colour terminals still work. `--sound` adds a terminal bell
when a thug raises his gun, when you hit someone and when you get shot.

## Controls

| Key | Action |
| --- | --- |
| SPACE, ENTER, F | fire at the reticle |
| UP / DOWN, W / S | choose difficulty on the title screen |
| 1, 2, 3 | start Rookie, Officer or Detective directly |
| 1 or 2 | between rounds: repair armor or upgrade weapon |
| P | pause |
| M | sound on / off |
| Q | back to title / quit |

## Rules of the beat

- The reticle (yellow brackets) sweeps the sidewalk by itself and bounces at
  the edges. It turns dark red while your weapon reloads.
- Thugs are red. Armored thugs are purple and take two hits (or one from a
  Magnum or better). Civilians wear bright colours and a tan face.
- A thug walks for a few seconds, then stops, flashes and shows a `!`. That is
  his aim time. Drop him before it runs out or he fires at the car. Dropping a
  thug while he is aiming is a clutch shot worth extra.
- Thugs who fire run for the edge of the screen. A thug that leaves the
  screen is gone, with no points.
- Hitting a civilian costs 250 points and a strike. Three strikes (two on
  Detective) and your badge is revoked. If a thug and a civilian overlap under
  the reticle, the thug takes the bullet.
- A round ends when you have dropped its quota of thugs. Then the shop opens:
  repair armor (+50, up to 100) or upgrade your weapon, never both.
- Armor at zero ends the game.

| Weapon | Reload | Damage | Spread |
| --- | --- | --- | --- |
| Pistol | 0.60 s | 1 | tight |
| Revolver | 0.40 s | 1 | tight |
| Magnum | 0.35 s | 2 | tight |
| Rifle | 0.25 s | 2 | wide (one extra cell each side) |
| Laser | 0.15 s | 3 | wide |

| Level | Sweep | Aim time | Damage | Miss chance | Strikes | Quota | Armored thugs from |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ROOKIE | slow | 1.20 s | 10 | 50 % | 3 | 4 + 1 per round | round 4 |
| OFFICER | medium | 0.85 s | 12 | 40 % | 3 | 5 + 2 per round | round 3 |
| DETECTIVE | fast | 0.75 s | 15 | 30 % | 2 | 6 + 2 per round | round 2 |

The sweep speeds up a little every round on every level. Best score per
difficulty is kept in `highscore.json`.

## Scoring

| Event | Points |
| --- | --- |
| Thug down | 100 |
| Armored thug down | 250 |
| Clutch shot (thug was aiming) | +50 |
| Civilian hit | -250 and a strike |

## Layout

| File | Contents |
| --- | --- |
| `beatcop/constants.py` | layout, tuning, difficulty and weapon tables, palette, sprites, logo font |
| `beatcop/engine.py` | game rules, no curses, runs headless for testing |
| `beatcop/render.py` | curses drawing, the title, shop, pause and end screens |
| `beatcop/__main__.py` | key handling and the main loop |
