from driver_setup import run as capture_board
from board_extractor import extract_state_with_recheck
from solver import solve, print_moves, print_state


def main():
    path = capture_board()

    model = extract_state_with_recheck(path, rows=3, cols=4)
    state = model.to_state()

    print("\nExtracted state:")
    print_state(state)

    moves = solve(state)

    if moves:
        print_moves(moves)
    else:
        print("No solution")


if __name__ == "__main__":
    main()