from __future__ import annotations

from display import pretty_moves, show_tubes
from search import solve


if __name__ == "__main__":
    # Replace this with the static puzzle combination you want to solve.
    # Bottom -> top.
    initial_state = (
        ("R", "G", "P", "C"),
        ("O", "M", "W", "Y"),
        ("Y", "B", "Y", "O"),
        ("P", "C", "W", "O"),
        ("C", "L", "R", "L"),
        ("O", "L", "M", "G"),
        ("W", "L", "R", "G"),
        ("M", "B", "P", "M"),
        ("Y", "C", "W", "R"),
        ("B", "B", "P", "G"),
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
