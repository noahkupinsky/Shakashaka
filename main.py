from package.io import scrape_board, load_board_from_image, load_board_from_text
from package.Solver import Solver

# board = scrape_board(5)
# board = load_board_from_text("error_board.txt")
board = load_board_from_image("examples/empty_10.png")


print(board)

solns = Solver(board).solve()

print(solns[0])
