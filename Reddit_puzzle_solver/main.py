from __future__ import annotations

from board_extractor import extract_state_with_recheck
from image_retriver import run as capture_board
from solver import print_moves, print_state, solve


def main() -> None:
    screenshot_path = capture_board()
    state = extract_state_with_recheck(screenshot_path, rows=3, cols=4)

    print("\nFinal extracted state:")
    print_state(state)

    moves = solve(state)

    if moves:
        print_moves(moves)
    else:
        print("No solution found")


if __name__ == "__main__":
    main()