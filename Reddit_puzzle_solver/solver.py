from __future__ import annotations

from collections import Counter
from math import inf
from typing import Dict, List, Optional, Tuple

from board_model import State, Tube

Move = Tuple[int, int]
CAPACITY = 4


def validate_state(state: State) -> tuple[bool, Counter]:
    counts = Counter(c for tube in state for c in tube)
    valid = len(counts) == 10 and all(v == 4 for v in counts.values())
    return valid, counts


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