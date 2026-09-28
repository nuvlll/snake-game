"""
Snake — tkinter edition (no installs needed)
Run: python snake.py
Controls: Arrow keys or WASD · SPACE to start/restart · ESC to quit
"""

import tkinter as tk
import random

# ── Layout ───────────────────────────────────────────────────────────────────
CELL     = 22
COLS     = 28
ROWS     = 20
W        = COLS * CELL
H        = ROWS * CELL
HUD      = 50
SPD_BASE = 130   # ms between steps (lower = faster)
SPD_MIN  =  60   # speed cap

# ── Palette ──────────────────────────────────────────────────────────────────
BG       = "#0D0E14"
GRID_COL = "#16171E"
HEAD_COL = "#50DC91"
BODY_COL = "#2DA55F"
FOOD_COL = "#FF4B4B"
HUD_BG   = "#12131C"
TEXT_COL = "#D2D7E6"
DIM_COL  = "#787990"

# ── Directions ────────────────────────────────────────────────────────────────
UP    = ( 0, -1)
DOWN  = ( 0,  1)
LEFT  = (-1,  0)
RIGHT = ( 1,  0)
OPPOSITE = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}

KEY_MAP = {
    "Up": UP,    "w": UP,
    "Down": DOWN, "s": DOWN,
    "Left": LEFT, "a": LEFT,
    "Right": RIGHT, "d": RIGHT,
}


def lerp_hex(c1, c2, t):
    """Interpolate between two hex colours."""
    r1, g1, b1 = int(c1[1:3],16), int(c1[3:5],16), int(c1[5:7],16)
    r2, g2, b2 = int(c2[1:3],16), int(c2[3:5],16), int(c2[5:7],16)
    r = int(r1 + (r2-r1)*t)
    g = int(g1 + (g2-g1)*t)
    b = int(b1 + (b2-b1)*t)
    return f"#{r:02x}{g:02x}{b:02x}"


class Snake:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Snake")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)

        self.canvas = tk.Canvas(root, width=W, height=H + HUD,
                                bg=BG, highlightthickness=0)
        self.canvas.pack()

        self.root.bind("<KeyPress>", self._on_key)

        self.high     = 0
        self.mode     = "start"
        self._job     = None

        self._reset()
        self._draw()

    # ── State ─────────────────────────────────────────────────────────────────
    def _reset(self):
        mid = (COLS // 2, ROWS // 2)
        self.snake     = [mid, (mid[0]-1, mid[1])]
        self.direction = RIGHT
        self.next_dir  = RIGHT
        self.food      = self._new_food()
        self.score     = 0
        self.speed     = SPD_BASE

    def _new_food(self):
        occupied = set(self.snake)
        free = [(x, y) for x in range(COLS) for y in range(ROWS)
                if (x, y) not in occupied]
        return random.choice(free)

    # ── Input ─────────────────────────────────────────────────────────────────
    def _on_key(self, event):
        key = event.keysym

        if self.mode == "start":
            if key == "space":
                self.mode = "playing"
                self._schedule()

        elif self.mode == "playing":
            d = KEY_MAP.get(key)
            if d and d != OPPOSITE.get(self.direction):
                self.next_dir = d

        elif self.mode == "dead":
            if key == "space":
                self._reset()
                self.mode = "playing"
                self._schedule()
            elif key == "Escape":
                self.root.destroy()

        self._draw()

    # ── Game loop ─────────────────────────────────────────────────────────────
    def _schedule(self):
        if self._job:
            self.root.after_cancel(self._job)
        self._job = self.root.after(self.speed, self._step)

    def _step(self):
        if self.mode != "playing":
            return

        self.direction = self.next_dir
        dx, dy   = self.direction
        hx, hy   = self.snake[0]
        new_head = (hx + dx, hy + dy)

        # Collision
        if (not (0 <= new_head[0] < COLS and 0 <= new_head[1] < ROWS)
                or new_head in self.snake):
            self.high = max(self.high, self.score)
            self.mode = "dead"
            self._draw()
            return

        self.snake.insert(0, new_head)
        if new_head == self.food:
            self.score += 10
            self.food   = self._new_food()
            self.speed  = max(SPD_MIN, SPD_BASE - (self.score // 50) * 12)
        else:
            self.snake.pop()

        self._draw()
        self._schedule()

    # ── Drawing ───────────────────────────────────────────────────────────────
    def _draw(self):
        cv = self.canvas
        cv.delete("all")

        # Background + grid
        cv.create_rectangle(0, 0, W, H, fill=BG, outline="")
        for x in range(0, W+1, CELL):
            cv.create_line(x, 0, x, H, fill=GRID_COL)
        for y in range(0, H+1, CELL):
            cv.create_line(0, y, W, y, fill=GRID_COL)

        if self.mode == "start":
            self._draw_overlay("SNAKE", HEAD_COL, [
                ("Press  SPACE  to start", TEXT_COL),
                ("Arrow keys / WASD  ·  eat red dots  ·  don't crash", DIM_COL),
            ])
            return

        # Food
        fx, fy = self.food
        p = 4
        cv.create_oval(fx*CELL+p, fy*CELL+p,
                       (fx+1)*CELL-p, (fy+1)*CELL-p,
                       fill=FOOD_COL, outline="")

        # Snake (head → tail colour gradient)
        n = len(self.snake)
        for i, (sx, sy) in enumerate(self.snake):
            t   = i / max(n-1, 1)
            col = lerp_hex(HEAD_COL, BODY_COL, t)
            pad = 3 if i == 0 else 4
            cv.create_rectangle(sx*CELL+pad, sy*CELL+pad,
                                 (sx+1)*CELL-pad, (sy+1)*CELL-pad,
                                 fill=col, outline="")

        # HUD bar
        cv.create_rectangle(0, H, W, H+HUD, fill=HUD_BG, outline="")
        cv.create_line(0, H, W, H, fill=GRID_COL)
        cv.create_text(18, H+HUD//2, text=f"Score  {self.score}",
                       fill=TEXT_COL, font=("Segoe UI", 13), anchor="w")
        cv.create_text(W-18, H+HUD//2, text=f"Best  {self.high}",
                       fill=DIM_COL, font=("Segoe UI", 13), anchor="e")

        if self.mode == "dead":
            self._draw_overlay("GAME OVER", FOOD_COL, [
                (f"Score  {self.score}   ·   Best  {self.high}", TEXT_COL),
                ("SPACE to restart  ·  ESC to quit", DIM_COL),
            ])

    def _draw_overlay(self, title, title_col, lines):
        cv = self.canvas
        # Stipple gives a darkened-glass effect without PIL
        cv.create_rectangle(0, 0, W, H+HUD,
                             fill="black", stipple="gray50", outline="")
        cy = (H + HUD) // 2 - 46
        cv.create_text(W//2, cy, text=title, fill=title_col,
                       font=("Segoe UI", 38, "bold"))
        cy += 58
        for text, col in lines:
            cv.create_text(W//2, cy, text=text, fill=col,
                           font=("Segoe UI", 13))
            cy += 30


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    root = tk.Tk()
    Snake(root)
    root.mainloop()

if __name__ == "__main__":
    main()
