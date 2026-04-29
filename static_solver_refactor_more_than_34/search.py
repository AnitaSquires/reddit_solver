from math import inf
from typing import Dict, List, Optional

from models import MAX_NODES, PRINT_EVERY, Move, State
from moves import legal_moves
from rules import apply_move, is_solved


class SolutionFound(Exception):
    pass


def heuristic(state: State) -> int:
    score = 0
    for tube in state:
        if not tube:
            continue

        # Ignore solved tubes
        if len(tube) == 4 and len(set(tube)) == 1:
            continue

        # Count color breaks (safe lower bound)
        blocks = 1
        for a, b in zip(tube, tube[1:]):
            if a != b:
                blocks += 1

        score += blocks - 1

    return score


def solve(initial: State) -> Optional[List[Move]]:
    """
    IDA* search with improvements:
    - Better heuristic
    - Backtrack pruning (no immediate undo moves)
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

        last_move = path[-1] if path else None

        for mv in legal_moves(state):
            # 🔴 Prevent immediate undo (A->B then B->A)
            if last_move and (mv[0] == last_move[1] and mv[1] == last_move[0]):
                continue

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
