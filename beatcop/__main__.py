"""Entry point: python3 -m beatcop [rookie|officer|detective] [--sound]"""
import curses
import locale
import os
import sys
import time

from .constants import *  # noqa: F401,F403
from .engine import Game, load_scores, save_scores
from .render import Renderer, title_screen, end_overlay


def read_keys(scr):
    out = []
    for _ in range(60):
        ch = scr.getch()
        if ch == -1:
            break
        if ch == curses.KEY_UP:
            out.append("up")
        elif ch == curses.KEY_DOWN:
            out.append("down")
        elif ch in (32, 10, 13, curses.KEY_ENTER):
            out.append("btn")
        elif 0 <= ch < 256:
            c = chr(ch).lower()
            out.append({"w": "up", "s": "down", "f": "btn"}.get(c, c))
    return out


def run(scr, start_sel, sound):
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    scr.nodelay(True)
    scr.keypad(True)
    curses.start_color()
    ui = Renderer(scr)
    scores = load_scores()
    state, sel = "title", start_sel
    game = None
    paused = False
    new_best = False
    frame = 0
    nxt = time.monotonic()
    while True:
        frame += 1
        rows, cols = scr.getmaxyx()
        keys = read_keys(scr)
        if "m" in keys:
            sound = not sound
        scr.erase()
        if rows < NEED_ROWS or cols < NEED_COLS:
            try:
                scr.addstr(0, 0, ("ENLARGE THE TERMINAL TO AT LEAST %dx%d (NOW %dx%d)"
                                  % (NEED_COLS, NEED_ROWS, cols, rows))[:max(1, cols - 1)])
            except curses.error:
                pass
            if "q" in keys:
                return
            scr.refresh()
            time.sleep(0.1)
            continue
        ui.layout(rows, cols)
        if state == "title":
            for k in keys:
                if k == "up":
                    sel = (sel - 1) % len(DIFFS)
                elif k == "down":
                    sel = (sel + 1) % len(DIFFS)
                elif k in ("1", "2", "3", "btn"):
                    if k != "btn":
                        sel = int(k) - 1
                    game, state, paused, new_best = Game(sel), "play", False, False
                    game.best = scores.get(game.d["name"], 0)
                    break
                elif k == "q":
                    return
            if state == "title":
                title_screen(ui, frame, sel, scores, sound)
        if state == "play":
            if "q" in keys:
                state = "title"
                title_screen(ui, frame, sel, scores, sound)
            else:
                if "p" in keys:
                    paused = not paused
                if not paused:
                    game.step(keys)
                    if sound and game.beep:
                        curses.beep()
                game.best = max(game.best, game.score)
                ui.draw(game, sound)
                if paused:
                    ui.pause_overlay()
                if game.result:
                    state = "over"
                    best = scores.get(game.d["name"], 0)
                    new_best = game.score > best
                    if new_best:
                        scores[game.d["name"]] = game.score
                        save_scores(scores)
        elif state == "over":
            for k in keys:
                if k == "btn":
                    state = "title"
                elif k == "q":
                    return
            game.step([])
            ui.draw(game, sound)
            end_overlay(ui, game, scores.get(game.d["name"], 0), new_best)
        scr.refresh()
        nxt += 1.0 / FPS
        delay = nxt - time.monotonic()
        if delay > 0:
            time.sleep(delay)
        else:
            nxt = time.monotonic()


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "-h" in argv or "--help" in argv:
        print("usage: python3 -m beatcop [rookie|officer|detective] [--sound]")
        return 0
    locale.setlocale(locale.LC_ALL, "")
    sound = "--sound" in argv
    sel = 1
    names = {"easy": 0, "rookie": 0, "normal": 1, "officer": 1, "hard": 2, "detective": 2}
    for a in argv:
        if a.lower() in names:
            sel = names[a.lower()]
    os.environ.setdefault("ESCDELAY", "25")
    if not os.environ.get("TERM"):
        os.environ["TERM"] = "xterm-256color"
    try:
        curses.wrapper(run, sel, sound)
    except KeyboardInterrupt:
        pass
    print("End of shift.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
