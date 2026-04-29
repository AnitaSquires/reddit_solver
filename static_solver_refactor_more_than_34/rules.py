from __future__ import annotations

from typing import Optional

from models import CAPACITY, State, Tube


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
    if not src:
        return False
    if len(dst) >= CAPACITY:
        return False
    return (not dst) or (dst[0] == src[0])


def apply_move(state: State, i: int, j: int) -> Optional[State]:
    if i == j:
        return None

    tubes = [list(t) for t in state]
    src = tubes[i]
    dst = tubes[j]

    if not can_pour(tuple(src), tuple(dst)):
        return None

    color = src[0]
    run = active_run_length(tuple(src))
    space = CAPACITY - len(dst)
    amount = min(run, space)

    if amount <= 0:
        return None

    moved = src[:amount]
    if any(c != color for c in moved):
        return None

    del src[:amount]
    dst[:0] = moved

    return tuple(tuple(t) for t in tubes)
