from driver_setup import run as capture_board
from board_extractor import extract_state_from_board
from solver import solve, print_moves, print_state


def main():
    # 1. Capture screenshot
    path = capture_board()

    # 2. Extract board state (colors → tokens)
    model = extract_state_from_board(path, rows=3, cols=4)
    state = model.to_state()

    print("\nExtracted state:")
    print_state(state)

    # 3. Solve puzzle
    moves = solve(state)

    if moves:
        print("\nSolution:")
        print_moves(moves)
    else:
        print("No solution found")


if __name__ == "__main__":
    main()