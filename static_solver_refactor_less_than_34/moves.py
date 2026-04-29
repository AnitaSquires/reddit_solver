from __future__ import annotations

from typing import List

from models import Move, State, CAPACITY
from rules import can_pour


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
