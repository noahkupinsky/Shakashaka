from package.Board import Board
from package.Loc import Loc
from typing import Set
from package.triangle_logic import DiagonalRectangleValidator
from package.empty_logic import validate_axis_rectangle
from package.number_logic import validate_number

    
class SolutionValidator:
    def __init__(self, board: Board):
        self.board = board
        self.visited: Set[Loc] = set()
        
    def validate(self, verbose: bool = False) -> bool:
        # First need to deal with diagonal rectangles, so that when we do axis rectangles, 
        # we're not looking at the empty cells inside the diagonal rectangles
        for loc, cell in self.board:
            if loc in self.visited:
                continue
            
            if cell.is_triangle:
                if not self._validate_diagonal_rectangle(loc):
                    if verbose:
                        print("Failed to validate diagonal rectangles.")
                    return False
            elif cell.is_undecided_or_empty:
                if not self._validate_axis_rectangle(loc):
                    if verbose:
                        print("Failed to validate axis rectangles.")
                    return False
            elif cell.is_number:
                if not self._validate_number(loc):
                    if verbose:
                        print("Failed to validate number cells.")
                    return False
        
        return True

    def _validate_diagonal_rectangle(self, loc: Loc) -> bool:
        # Create a diagonal rectangle from the triangle
        diagonal_rectangle = DiagonalRectangleValidator(self.board)
        if not diagonal_rectangle.validate(loc):
            return False
        
        # Add to the processed sets
        self.visited.update(diagonal_rectangle.validated_locs)

        return True
            
    def _validate_axis_rectangle(self, loc: Loc) -> bool:
        is_valid, visited = validate_axis_rectangle(self.board, loc)
        
        if not is_valid:
            return False
        # Add to the processed set
        self.visited.update(visited)

        return True
    
    def _validate_number(self, loc: Loc) -> bool:
        if not validate_number(self.board, loc):
            return False

        return True
