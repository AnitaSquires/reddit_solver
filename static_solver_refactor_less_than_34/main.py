from __future__ import annotations

from display import pretty_moves, show_tubes
from search import solve


if __name__ == "__main__":
    # Replace this with the static puzzle combination you want to solve.
    # Bottom -> top.
    initial_state = (
        ("W", "G", "M", "Y"),
        ("L", "C", "G", "B"),
        ("O", "W", "G", "W"),
        ("P", "W", "L", "P"),
        ("O", "L", "B", "G"),
        ("B", "R", "R", "Y"),
        ("O", "R", "L", "M"),
        ("Y", "Y", "P", "R"),
        ("M", "C", "P", "M"),
        ("B", "C", "O", "C"),
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
