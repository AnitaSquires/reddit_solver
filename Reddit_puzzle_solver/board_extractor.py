from __future__ import annotations
from Reddit_puzzle_solver.board_model import BoardModel

import cv2
import numpy as np


# ----------------------------------------
# CONFIG
# ----------------------------------------
PATCH_RADIUS = 4

PALETTE = {
    "R": (236, 72, 57),
    "P": (127, 30, 133),
    "M": (236, 72, 248),
    "W": (151, 152, 156),
    "L": (74, 78, 171),
    "O": (243, 178, 80),
    "B": (10, 10, 245),
    "C": (122, 246, 253),
    "Y": (255, 255, 114),
    "G": (86, 179, 64),
}


# ----------------------------------------
# HELPERS
# ----------------------------------------
def patch_rgb(img, x, y, radius=PATCH_RADIUS):
    h, w, _ = img.shape

    x = max(0, min(w - 1, x))
    y = max(0, min(h - 1, y))

    x1 = max(0, x - radius)
    y1 = max(0, y - radius)
    x2 = min(w, x + radius + 1)
    y2 = min(h, y + radius + 1)

    patch = img[y1:y2, x1:x2]

    if patch.size == 0:
        return (0, 0, 0)

    med = np.median(patch.reshape(-1, 3), axis=0)
    return int(med[0]), int(med[1]), int(med[2])


def closest_color(rgb):
    best = None
    best_dist = float("inf")

    for token, ref in PALETTE.items():
        dist = sum((a - b) ** 2 for a, b in zip(rgb, ref))
        if dist < best_dist:
            best_dist = dist
            best = token

    return best


def is_empty(rgb):
    return max(rgb) < 60


# ----------------------------------------
# MAIN EXTRACTION
# ----------------------------------------
def extract_state_from_board(path: str, rows: int = 3, cols: int = 4):
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(path)

    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    h, w = img.shape[:2]

    # Crop to remove UI padding
    board = img[
        int(h * 0.12): int(h * 0.88),
        int(w * 0.12): int(w * 0.88),
    ]

    cv2.imwrite("debug_board.png", cv2.cvtColor(board, cv2.COLOR_RGB2BGR))

    model = BoardModel(rows=rows, cols=cols, forced_empty_columns=2)

    # 🔥 USE YOUR EXISTING GRID SYSTEM (THIS IS THE FIX)
    model.update_board(board, sampler=patch_rgb)

    # ----------------------------------------
    # Convert RGB → tokens
    # ----------------------------------------
    for column in model.columns:
        if column.forced_empty:
            continue

        for i, rgb in enumerate(column.slot_rgbs):
            if rgb is None:
                continue

            if is_empty(rgb):
                token = None
            else:
                token = closest_color(rgb)

            column.set_token(i, token)

    # ----------------------------------------
    # Debug visualization
    # ----------------------------------------
    debug = board.copy()

    for column in model.columns:
        if column.forced_empty:
            continue

        for rgb in column.slot_rgbs:
            pass  # RGB already stored; we draw via update_board coords

    cv2.imwrite("debug_sampling.png", cv2.cvtColor(debug, cv2.COLOR_RGB2BGR))

    return model