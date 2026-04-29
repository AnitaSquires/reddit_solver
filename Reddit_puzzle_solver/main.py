from board_extractor import extract_state_with_recheck
from driver_setup import run as capture_board
from solver import print_moves, print_state, solve
from puzzle_button import PuzzleButton


def main() -> None:
    screenshot_path = capture_board()

    # ✅ now correctly returns BoardModel
    model = extract_state_with_recheck(screenshot_path, rows=3, cols=4)

    # Debug UI layer
    buttons = [PuzzleButton(col) for col in model.columns]

    print("\nDebug: First column slots:")
    print(buttons[0].slot_one)
    print(buttons[0].slot_two)
    print(buttons[0].slot_three)
    print(buttons[0].slot_four)

    # Solver layer
    state = model.to_state()

    print("\nFinal extracted state:")
    print_state(state)

    moves = solve(state)

    if moves:
        print_moves(moves)
    else:
        print("No solution found")


if __name__ == "__main__":
    main()