from __future__ import annotations
from typing import List, Tuple, Iterator

from package.Loc import Loc
from package.Cell import Cell, Cells

type LocCell = Tuple[Loc, Cell]
type BoardSection = Cell | List[Cell] | List[List[Cell]]

class Board:
    BORDER_CHAR = '▢'
    PRINT_SPACING = 1
    
    def __init__(self, board: List[List[Cell]]):
        self.size = len(board)
        self.board = board
        
    def __str__(self):
        border_row = [Board.BORDER_CHAR] * (self.size + 2)
        string_board = [border_row]
        for y in range(self.size):
            string_row = [Board.BORDER_CHAR] + [str(self.board[x][y]) for x in range(self.size)] + [Board.BORDER_CHAR]
            string_board.append(string_row)
        string_board.append(border_row)
        
        # make 0, 0 the bottom left
        string_board.reverse()
        return "\n".join((" " * Board.PRINT_SPACING).join(row) for row in string_board)
    
    def __repr__(self) -> str:
        return 'Board:\n' + str(self) + '\n'

    def __getitem__(self, key: any) -> BoardSection:
        if isinstance(key, Loc):
            if not key.is_integral():
                raise IndexError("Loc must have integral coordinates")
            return self._get_cell(int(key.x), int(key.y))
        elif isinstance(key, tuple):
            if len(key) != 2:
                raise IndexError("Expected tuple key to be length 2")
            return self._get_cell(key[0], key[1])
        elif isinstance(key, int) or isinstance(key, slice):
            # no special behavior
            return self.board[key]
        else:
            raise IndexError("Invalid key type for Board access. Use Loc, tuple of two integers, int, or slice.")

    def _get_cell(self, x: int, y: int) -> Cell:
        """Get a cell at the specified coordinates, returning a black cell if out of bounds."""
        if 0 <= x < self.size and 0 <= y < self.size:
            return self.board[x][y]
        return Cells.BLACK 

    def __setitem__(self, key: any, value: BoardSection):
        if isinstance(key, Loc):
            if not key.is_integral():
                raise IndexError("Loc must have integral coordinates")
            self._set_cell(int(key.x), int(key.y), value)
        elif isinstance(key, tuple):
            if len(key) != 2:
                raise IndexError("Expected tuple key to be length 2")
            x, y = key
            self._set_cell(x, y, value)
        else:
            self.board[key] = value
            
    def _set_cell(self, x: int, y: int, value: Cell):
        """Set a cell at the specified coordinates, ignoring out of bounds."""
        if 0 <= x < self.size and 0 <= y < self.size:
            self.board[x][y] = value
        # else ignore out of bounds
            
    def __len__(self) -> int:
        return self.size

    def __iter__(self) -> Iterator[LocCell]:
        for x in range(self.size):
            for y in range(self.size):
                yield (Loc(x, y), self.board[x][y])
    
    def copy(self) -> Board:
        """Create a deep copy of the board."""
        new_board = [[cell for cell in row] for row in self.board]
        return Board(new_board)


def undecided_board(size: int) -> Board:
    """Create an empty board of the given size."""
    return Board([[Cells.UNDECIDED for _ in range(size)] for _ in range(size)])