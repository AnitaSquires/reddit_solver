from __future__ import annotations

from collections import Counter
from typing import Tuple

import cv2
import numpy as np

from board_model import BoardModel, State

RGB = Tuple[int, int, int]

PATCH_RADIUS = 4
SAMPLE_Y_FRACS = [0.15, 0.38, 0.62, 0.85]
SLOT_SAMPLE_OFFSETS = [-0.08, 0.0, 0.08]

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


# ----------------------------------------
# IMAGE HELPERS
# ----------------------------------------
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


def is_empty_rgb(rgb: RGB, empty_max_channel: int) -> bool:
    r, g, b = rgb

    if max(r, g, b) < empty_max_channel:
        return True

    mn = min(r, g, b)
    mx = max(r, g, b)
    if mx > 170 and (mx - mn) < 18:
        return True

    return False


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


# ----------------------------------------
# TUBE DETECTION (NEW CORE LOGIC)
# ----------------------------------------
def find_tube_columns(board: np.ndarray, cols: int) -> list[int]:
    col_strength = np.mean(board, axis=0)
    col_strength = cv2.GaussianBlur(col_strength, (31, 1), 0)

    peaks = np.argsort(col_strength)[-cols:]
    return sorted(peaks.tolist())


def find_tube_rows(board: np.ndarray, rows: int) -> list[int]:
    row_strength = np.mean(board, axis=1)
    row_strength = cv2.GaussianBlur(row_strength, (1, 31), 0)

    peaks = np.argsort(row_strength)[-rows:]
    return sorted(peaks.tolist())


# ----------------------------------------
# MAIN EXTRACTION
# ----------------------------------------
def extract_state_from_board(
    path: str, empty_max_channel: int, rows: int = 3, cols: int = 4
) -> BoardModel:

    img_bgr = cv2.imread(path)
    if img_bgr is None:
        raise FileNotFoundError(f"Could not read image: {path}")

    img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    # Crop UI padding
    h, w = img.shape[:2]
    board = img[
        int(h * 0.12): int(h * 0.88),
        int(w * 0.12): int(w * 0.88),
    ]

    cv2.imwrite("debug_cropped_board.png", cv2.cvtColor(board, cv2.COLOR_RGB2BGR))

    model = BoardModel(rows=rows, cols=cols, forced_empty_columns=2)

    # 🔥 Detect real tube positions
    col_centers = find_tube_columns(board, cols)
    row_centers = find_tube_rows(board, rows)

    for column in model.columns:
        if column.forced_empty:
            column.clear()
            continue

        cx = col_centers[column.col]
        cy_base = row_centers[column.row]

        for slot_index, frac in enumerate(SAMPLE_Y_FRACS):
            cy = int(cy_base + (frac - 0.5) * 90)

            rgb = patch_rgb(board, cx, cy)
            token = classify_slot(board, cx, cy, 40, empty_max_channel)

            column.set_rgb(slot_index, rgb)
            column.set_token(slot_index, token)

            cv2.circle(board, (cx, cy), 3, (255, 0, 0), -1)

    cv2.imwrite("debug_sampling.png", cv2.cvtColor(board, cv2.COLOR_RGB2BGR))

    return model


# ----------------------------------------
# VALIDATION
# ----------------------------------------
def validate_state(state: State, forced_empty_columns: int = 2):
    counts = Counter(c for tube in state for c in tube)
    valid_counts = len(counts) == 10 and all(v == 4 for v in counts.values())
    valid_trailing_empties = all(not tube for tube in state[-forced_empty_columns:])
    return valid_counts and valid_trailing_empties, counts


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