from __future__ import annotations

from collections import Counter
from math import inf
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

Tube = Tuple[str, ...]
State = Tuple[Tube, ...]
Move = Tuple[int, int]

BOARD_PATH = "puzzle_board.png"
CAPACITY = 4

GRID_ROWS = 3
GRID_COLS = 4

SAMPLE_Y_FRACS = [0.16, 0.41, 0.66, 0.88]
PATCH_RADIUS = 3

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

EMPTY_MAX_CHANNEL_OPTIONS = [60, 70, 80, 90]


def luminance(r: int, g: int, b: int) -> float:
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def saturation(r: int, g: int, b: int) -> float:
    mx = max(r, g, b)
    mn = min(r, g, b)
    if mx == 0:
        return 0.0
    return (mx - mn) / mx


def patch_rgb(img: np.ndarray, x: int, y: int, radius: int = PATCH_RADIUS) -> Tuple[int, int, int]:
    h, w, _ = img.shape
    x1 = max(0, x - radius)
    y1 = max(0, y - radius)
    x2 = min(w, x + radius + 1)
    y2 = min(h, y + radius + 1)

    patch = img[y1:y2, x1:x2].reshape(-1, 3)
    med = np.median(patch, axis=0)
    return int(med[0]), int(med[1]), int(med[2])


def is_empty_sample(r: int, g: int, b: int, empty_max_channel: int) -> bool:
    return max(r, g, b) < empty_max_channel


def closest_color(r: int, g: int, b: int) -> str:
    best_token = "?"
    best_dist = float("inf")

    for token, (tr, tg, tb) in PALETTE.items():
        dist = (r - tr) ** 2 + (g - tg) ** 2 + (b - tb) ** 2
        if dist < best_dist:
            best_dist = dist
            best_token = token

    return best_token


def extract_state_from_board(path: str, empty_max_channel: int) -> State:
    img_bgr = cv2.imread(path)
    if img_bgr is None:
        raise FileNotFoundError(f"Could not read image: {path}")

    img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    h, w, _ = img.shape

    grid_left, grid_right = 0.05, 0.95
    grid_top, grid_bottom = 0.12, 0.83

    cell_w = (grid_right - grid_left) * w / GRID_COLS
    cell_h = (grid_bottom - grid_top) * h / GRID_ROWS
    start_x = grid_left * w
    start_y = grid_top * h

    tubes: List[Tube] = []

    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            cell_x = start_x + col * cell_w
            cell_y = start_y + row * cell_h
            cx = int(round(cell_x + cell_w * 0.50))

            top_to_bottom: List[str] = []

            for frac in SAMPLE_Y_FRACS:
                cy = int(round(cell_y + cell_h * frac))
                r, g, b = patch_rgb(img, cx, cy)

                if is_empty_sample(r, g, b, empty_max_channel):
                    continue

                top_to_bottom.append(closest_color(r, g, b))

            if not top_to_bottom:
                tubes.append(())
            else:
                tubes.append(tuple(reversed(top_to_bottom)))

    return tuple(tubes)


def validate_state(state: State) -> tuple[bool, Counter]:
    counts = Counter(c for tube in state for c in tube)
    valid = len(counts) == 10 and all(v == 4 for v in counts.values())
    return valid, counts


def extract_state_with_recheck(path: str) -> State:
    last_state: Optional[State] = None

    for empty_max_channel in EMPTY_MAX_CHANNEL_OPTIONS:
        state = extract_state_from_board(path, empty_max_channel)
        valid, counts = validate_state(state)

        print(f"\nTrying EMPTY_MAX_CHANNEL={empty_max_channel}")
        print("Counts:", dict(counts))
        print("State:")
        print_state(state)

        last_state = state

        if valid:
            print("Board validated successfully.")
            return state

    raise ValueError(
        "Could not extract a valid board state. "
        "Colour counts did not balance after retries."
    )


def is_solved(state: State) -> bool:
    for tube in state:
        if not tube:
            continue
        if len(tube) != CAPACITY:
            return False
        if len(set(tube)) != 1:
            return False
    return True


def active_run_length(tube: Tube) -> int:
    if not tube:
        return 0
    c = tube[0]
    n = 1
    for i in range(1, len(tube)):
        if tube[i] == c:
            n += 1
        else:
            break
    return n


def can_pour(src: Tube, dst: Tube) -> bool:
    return bool(src) and len(dst) < CAPACITY and (not dst or dst[0] == src[0])


def apply_move(state: State, i: int, j: int) -> Optional[State]:
    if i == j:
        return None

    tubes = [list(t) for t in state]
    src = tubes[i]
    dst = tubes[j]

    if not can_pour(tuple(src), tuple(dst)):
        return None

    run = active_run_length(tuple(src))
    amount = min(run, CAPACITY - len(dst))

    if amount <= 0:
        return None

    moved = src[:amount]
    del src[:amount]
    dst[:0] = moved

    return tuple(tuple(t) for t in tubes)


def legal_moves(state: State) -> List[Move]:
    moves: List[Move] = []
    n = len(state)

    for i in range(n):
        if not state[i]:
            continue

        seen_empty = False

        for j in range(n):
            if i == j:
                continue
            if not can_pour(state[i], state[j]):
                continue

            if not state[j]:
                if seen_empty:
                    continue
                seen_empty = True

            moves.append((i, j))

    return moves


def heuristic(state: State) -> int:
    score = 0
    for tube in state:
        if not tube:
            continue
        if len(tube) == CAPACITY and len(set(tube)) == 1:
            continue

        blocks = 1
        for a, b in zip(tube, tube[1:]):
            if a != b:
                blocks += 1
        score += blocks - 1

    return score


class SolutionFound(Exception):
    pass


def solve(initial: State) -> Optional[List[Move]]:
    path: List[Move] = []
    solution: Optional[List[Move]] = None

    def search(state: State, g: int, threshold: int, seen: Dict[State, int]) -> int:
        nonlocal solution

        f = g + heuristic(state)
        if f > threshold:
            return f

        if is_solved(state):
            solution = path.copy()
            raise SolutionFound

        prev_best = seen.get(state)
        if prev_best is not None and prev_best <= g:
            return inf
        seen[state] = g

        minimum = inf

        for mv in legal_moves(state):
            nxt = apply_move(state, mv[0], mv[1])
            if nxt is None:
                continue

            path.append(mv)
            result = search(nxt, g + 1, threshold, seen)
            path.pop()

            if result < minimum:
                minimum = result

        return minimum

    threshold = heuristic(initial)

    while True:
        seen: Dict[State, int] = {}

        try:
            result = search(initial, 0, threshold, seen)
        except SolutionFound:
            return solution

        if result == inf:
            return None

        threshold = int(result)


def print_state(state: State) -> None:
    print("initial_state = (")
    for tube in state:
        print(f"    {tube if tube else '()'},")
    print(")")


def print_moves(moves: List[Move]) -> None:
    print(f"\nSolved in {len(moves)} moves:")
    for i, (a, b) in enumerate(moves, 1):
        print(f"{i}. {a + 1} -> {b + 1}")


if __name__ == "__main__":
    state = extract_state_with_recheck(BOARD_PATH)

    print("\nFinal extracted state:")
    print_state(state)

    moves = solve(state)

    if moves:
        print_moves(moves)
    else:
        print("No solution found")