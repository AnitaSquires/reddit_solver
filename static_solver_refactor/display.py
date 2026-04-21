from __future__ import annotations

from models import Move, State


def pretty_moves(moves: list[Move]) -> None:
    for i, (a, b) in enumerate(moves, 1):
        print(f"{i}. {a + 1} -> {b + 1}")


def show_tubes(state: State) -> None:
    for idx, tube in enumerate(state):
        print(f"{idx}: {list(tube)}")
