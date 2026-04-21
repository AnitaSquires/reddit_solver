from __future__ import annotations

from math import inf
from typing import List, Tuple, Optional, Dict

Tube = Tuple[str, ...]          # bottom -> top
State = Tuple[Tube, ...]
Move = Tuple[int, int]          # (from_tube, to_tube)

CAPACITY = 4
PRINT_EVERY = 100_000
MAX_NODES = 10_000_000


class SolutionFound(Exception):
    pass


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


def legal_moves(state: State) -> List[Move]:
    moves: List[Move] = []
    n = len(state)

    for i in range(n):
        if not state[i]:
            continue

        if len(state[i]) == CAPACITY and len(set(state[i])) == 1:
            continue

        seen_empty = False

        for j in range(n):
            if i == j:
                continue
            if not can_pour(state[i], state[j]):
                continue

            # Empty tubes are symmetric; keep only one empty destination per source.
            if not state[j]:
                if seen_empty:
                    continue
                seen_empty = True

            moves.append((i, j))

    return moves


def heuristic(state: State) -> int:
    """
    Small admissible heuristic:
    count the number of color blocks that still need merging.
    """
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


def solve(initial: State) -> Optional[List[Move]]:
    """
    IDA* search. Returns the move list, or None if no solution is found.
    """
    path: List[Move] = []
    nodes = 0
    solution: Optional[List[Move]] = None

    def search(state: State, g: int, threshold: int, seen: Dict[State, int]) -> int:
        nonlocal nodes, solution

        nodes += 1
        if MAX_NODES is not None and nodes >= MAX_NODES:
            raise RuntimeError(f"Stopped after {MAX_NODES} nodes without finding a solution.")

        if PRINT_EVERY and nodes % PRINT_EVERY == 0:
            print(f"Explored: {nodes}, depth: {g}, threshold: {threshold}")

        f = g + heuristic(state)
        if f > threshold:
            return f

        if is_solved(state):
            solution = path.copy()
            raise SolutionFound

        prev_best_g = seen.get(state)
        if prev_best_g is not None and prev_best_g <= g:
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
        print(f"\nStarting iteration with threshold: {threshold}")
        seen: Dict[State, int] = {}

        try:
            result = search(initial, 0, threshold, seen)
        except SolutionFound:
            print(f"Solved after exploring {nodes} states")
            return solution
        except RuntimeError as e:
            print(str(e))
            return None

        if result == inf:
            print("No solution found.")
            return None

        print(f"Increasing threshold -> {result}")
        threshold = int(result)


def pretty_moves(moves: List[Move]) -> None:
    for i, (a, b) in enumerate(moves, 1):
        print(f"{i}. {a + 1} -> {b + 1}")


def show_tubes(state: State) -> None:
    for idx, tube in enumerate(state):
        print(f"{idx}: {list(tube)}")


if __name__ == "__main__":
    # Replace this with the static puzzle combination you want to solve.
    # Bottom -> top.
    initial_state: State = (
    ("P", "Y", "M", "G"),
    ("B", "W", "P", "R"),
    ("R", "C", "B", "P"),
    ("G", "Y", "G", "O"),
    ("L", "W", "M", "G"),
    ("B", "W", "Y", "M"),
    ("Y", "B", "C", "C"),
    ("C", "O", "R", "W"),
    ("L", "R", "O", "P"),
    ("M", "L", "L", "O"),
    (),
    (),
    )

    print("Starting board:")
    show_tubes(initial_state)

    moves = solve(initial_state)

    if moves is None:
        print("No solution returned.")
    else:
        print(f"\nSolved in {len(moves)} moves:")
        pretty_moves(moves)