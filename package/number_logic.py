from package.Board import Board
from package.Loc import Loc
from package.Undecided import Undecided
from package.Cell import Cell, Cells
from package.util import AXIS_NEIGHBORS


def validate_number(board: Board, loc: Loc) -> bool:
    """
    Validate that the number cell at loc has the correct number of adjacent triangles.
    """
    if not board[loc].is_number:
        raise ValueError(f"Cell at {loc} is not a number cell.")

    adjacent_triangles = 0
    for delta in AXIS_NEIGHBORS:
        neighbor_loc = loc + delta
        if board[neighbor_loc].is_triangle:
            adjacent_triangles += 1

    return adjacent_triangles == board[loc].number

def update_opts_around_number(board: Board, undecided: Undecided, loc: Loc, cell: Cell) -> bool:
    # Update the possibilities of surrounding cells based on the new cell
    if not cell.is_number:
        raise ValueError("Called update_opts_around_number with a non-number cell")
    
    required_triangles = cell.number
    required_nontriangles = 4 - required_triangles
    num_nontriangles = 0
    num_triangles = 0
    undecided_neighbors = []
    
    for delta in AXIS_NEIGHBORS:
        neighbor_loc = loc + delta
        neighbor_cell = board[neighbor_loc]

        if neighbor_cell == Cells.UNDECIDED:
            undecided_neighbors.append(neighbor_loc)
        elif neighbor_cell.is_triangle:
            num_triangles += 1
        else:
            num_nontriangles += 1

    if num_triangles > required_triangles or num_nontriangles > required_nontriangles:
        return False
    
    if num_triangles == required_triangles:
        # all undecided neighbors must be empty
        for undecided_loc in undecided_neighbors:
            if not undecided.keep_opts(undecided_loc, Cells.DECIDED_EMPTY):
                return False
            
    if num_nontriangles == required_nontriangles:
        # all undecided neighbors must be triangles
        for undecided_loc in undecided_neighbors:
            if not undecided.remove_opts(undecided_loc, Cells.DECIDED_EMPTY):
                return False
    
    return True