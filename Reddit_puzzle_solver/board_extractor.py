from __future__ import annotations

from collections import Counter
from typing import Optional, Tuple

import cv2
import numpy as np

from board_model import BoardModel, State

RGB = Tuple[int, int, int]

PATCH_RADIUS = 4
SAMPLE_Y_FRACS = [0.18, 0.43, 0.67, 0.90]
SLOT_SAMPLE_OFFSETS = [-0.18, -0.08, 0.0, 0.08, 0.18]

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

EMPTY_MAX_CHANNEL_OPTIONS = [55, 65, 75, 85]


def patch_rgb(img: np.ndarray, x: int, y: int, radius: int = PATCH_RADIUS) -> RGB:
    h, w, _ = img.shape
    x1 = max(0, x - radius)
    y1 = max(0, y - radius)
    x2 = min(w, x + radius + 1)
    y2 = min(h, y + radius + 1)

    patch = img[y1:y2, x1:x2].reshape(-1, 3)
    med = np.median(patch, axis=0)
    return int(med[0]), int(med[1]), int(med[2])


def rgb_to_lab(rgb: RGB) -> Tuple[int, int, int]:
    arr = np.uint8([[[rgb[0], rgb[1], rgb[2]]]])
    lab = cv2.cvtColor(arr, cv2.COLOR_RGB2LAB)[0, 0]
    return int(lab[0]), int(lab[1]), int(lab[2])


PALETTE_LAB = {token: rgb_to_lab(rgb) for token, rgb in PALETTE.items()}


def is_empty_rgb(rgb: RGB, empty_max_channel: int) -> bool:
    r, g, b = rgb

    if max(r, g, b) < empty_max_channel:
        return True

    mn = min(r, g, b)
    mx = max(r, g, b)
    if mx > 170 and (mx - mn) < 18:
        return True

    return False


def closest_color(rgb: RGB) -> str:
    lab = rgb_to_lab(rgb)
    best_token = "?"
    best_dist = float("inf")

    for token, pal_lab in PALETTE_LAB.items():
        dist = (
            (lab[0] - pal_lab[0]) ** 2
            + (lab[1] - pal_lab[1]) ** 2
            + (lab[2] - pal_lab[2]) ** 2
        )
        if dist < best_dist:
            best_dist = dist
            best_token = token

    return best_token


def detect_board_bounds(img: np.ndarray) -> tuple[int, int, int, int]:
    lum = 0.2126 * img[:, :, 0] + 0.7152 * img[:, :, 1] + 0.0722 * img[:, :, 2]
    mask = (lum < 95).astype(np.uint8)

    kernel = np.ones((9, 9), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    num_labels, _, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)

    best_idx = -1
    best_area = 0
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if area > best_area:
            best_area = area
            best_idx = i

    if best_idx == -1 or best_area < 10000:
        return 0, 0, img.shape[1], img.shape[0]

    x = stats[best_idx, cv2.CC_STAT_LEFT]
    y = stats[best_idx, cv2.CC_STAT_TOP]
    w = stats[best_idx, cv2.CC_STAT_WIDTH]
    h = stats[best_idx, cv2.CC_STAT_HEIGHT]

    pad = 10
    x0 = max(0, x - pad)
    y0 = max(0, y - pad)
    x1 = min(img.shape[1], x + w + pad)
    y1 = min(img.shape[0], y + h + pad)

    return x0, y0, x1, y1


def classify_slot(img, cx, cy, cell_w, empty_max_channel):
    votes = []

    for dx_frac in SLOT_SAMPLE_OFFSETS:
        x = int(round(cx + dx_frac * cell_w))
        rgb = patch_rgb(img, x, cy)

        if is_empty_rgb(rgb, empty_max_channel):
            continue

        votes.append(closest_color(rgb))

    if not votes:
        return None

    return Counter(votes).most_common(1)[0][0]


# ✅ FIXED: now returns BoardModel
def extract_state_from_board(path: str, empty_max_channel: int, rows: int = 3, cols: int = 4) -> BoardModel:
    img_bgr = cv2.imread(path)
    if img_bgr is None:
        raise FileNotFoundError(f"Could not read image: {path}")

    img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    x0, y0, x1, y1 = detect_board_bounds(img)
    board = img[y0:y1, x0:x1]

    model = BoardModel(rows=rows, cols=cols, forced_empty_columns=2)

    board_h, board_w, _ = board.shape
    cell_w = board_w / cols
    cell_h = board_h / rows

    for column in model.columns:
        if column.forced_empty:
            column.clear()
            continue

        cx = int(round((column.col + 0.5) * cell_w))
        cell_top = column.row * cell_h

        for slot_index, frac in enumerate(SAMPLE_Y_FRACS):
            cy = int(round(cell_top + frac * cell_h))

            rgb = patch_rgb(board, cx, cy)
            token = classify_slot(board, cx, cy, cell_w, empty_max_channel)

            column.set_rgb(slot_index, rgb)
            column.set_token(slot_index, token)

    return model


def validate_state(state: State, forced_empty_columns: int = 2):
    counts = Counter(c for tube in state for c in tube)
    valid_counts = len(counts) == 10 and all(v == 4 for v in counts.values())
    valid_trailing_empties = all(not tube for tube in state[-forced_empty_columns:])
    return valid_counts and valid_trailing_empties, counts


# ✅ CLEANED + FIXED
def extract_state_with_recheck(path: str, rows: int = 3, cols: int = 4) -> BoardModel:
    for empty_max_channel in EMPTY_MAX_CHANNEL_OPTIONS:
        model = extract_state_from_board(path, empty_max_channel, rows=rows, cols=cols)
        state = model.to_state()

        valid, counts = validate_state(state, forced_empty_columns=2)

        print(f"\nTrying EMPTY_MAX_CHANNEL={empty_max_channel}")
        print("Counts:", dict(counts))
        print("State:")
        print_state(state)

        if valid:
            print("Board validated successfully.")
            return model

    raise ValueError("Could not extract a valid board state.")


def print_state(state: State) -> None:
    print("initial_state = (")
    for tube in state:
        print(f"    {tube if tube else '()'},")
    print(")")