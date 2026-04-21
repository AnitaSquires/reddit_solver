from __future__ import annotations

from display import pretty_moves, show_tubes
from search import solve


if __name__ == "__main__":
    # Replace this with the static puzzle combination you want to solve.
    # Bottom -> top.
    initial_state = (
        ("Y", "C", "Y", "P"),
        ("R", "G", "B", "L"),
        ("L", "M", "G", "W"),
        ("O", "B", "Y", "L"),
        ("C", "O", "W", "G"),
        ("P", "L", "G", "W"),
        ("O", "O", "R", "M"),
        ("P", "Y", "C", "W"),
        ("B", "M", "R", "C"),
        ("R", "B", "M", "P"),
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
