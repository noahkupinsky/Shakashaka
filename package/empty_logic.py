from package.Board import Board
from package.Cell import Cell, Cells
from package.Loc import Loc
from typing import Set, Callable
from package.Undecided import Undecided
from package.util import AXIS_NEIGHBORS

def get_connected_satisfying_condition(board: Board, loc: Loc, condition: Callable[[Cell], bool]) -> list[Loc]:
    visited = set()
    to_visit = [loc]
    satisfying = set()

    while to_visit:
        current = to_visit.pop()
        if current in visited:
            continue
        visited.add(current)

        if current == loc or condition(board[current]):
            satisfying.add(current)

            for delta in AXIS_NEIGHBORS:
                neighbor = current + delta
                if neighbor not in visited:
                    to_visit.append(neighbor)

    return satisfying

def axis_rectangle_closure(loc_set: set[Loc]) -> set[Loc]:
    if not loc_set:
        raise ValueError("Expected non-empty set")

    x_min = int(min(loc.x for loc in loc_set))
    x_max = int(max(loc.x for loc in loc_set))
    y_min = int(min(loc.y for loc in loc_set))
    y_max = int(max(loc.y for loc in loc_set))

    return {Loc(x, y) for x in range(x_min, x_max + 1) for y in range(y_min, y_max + 1)}

def diagonal_rectangle_closure(loc_set: set[Loc]) -> set[Loc]:
    """
    translate to diagonal coordinates, find the axis rectangle closure, and translate back
    x = (0.5, -0.5), y = (0.5, 0.5)
    """
    diagonal_locs = {Loc(loc.x - loc.y, loc.x + loc.y) for loc in loc_set}
    diagonal_closure_in_diagonal_coords = axis_rectangle_closure(diagonal_locs)
    diagonal_closure_in_axis_coords = set()
    for loc in diagonal_closure_in_diagonal_coords:
        axis_coords = 0.5 * Loc(loc.x + loc.y, -loc.x + loc.y)
        if axis_coords.is_integral():
            diagonal_closure_in_axis_coords.add(axis_coords)
            
    return diagonal_closure_in_axis_coords
    

def set_forms_rectangle(loc_set: set[Loc]) -> bool:
    if not loc_set:
        raise ValueError("expected non-empty set")

    expected = axis_rectangle_closure(loc_set)
    return expected == loc_set

def validate_axis_rectangle(board: Board, initial_empty_loc: Loc) -> bool:
    if not board[initial_empty_loc].is_undecided_or_empty:
        return False

    connected = get_connected_satisfying_condition(board, initial_empty_loc, lambda cell: cell.is_undecided_or_empty)

    return set_forms_rectangle(connected), connected
    
    
def is_empty_still_possible(board: Board, undecided: Undecided, loc: Loc) -> bool:
    connected_decided_empty = get_connected_satisfying_condition(board, loc, lambda cell: cell == Cells.DECIDED_EMPTY)
    
    axis_closure = axis_rectangle_closure(connected_decided_empty)
    diagonal_closure = diagonal_rectangle_closure(connected_decided_empty)
    minimum_closure = axis_closure.intersection(diagonal_closure)

    for loc in minimum_closure:
        # all cells in the closure must have the possibility of being empty
        cell = board[loc]

        if cell == Cells.UNDECIDED:
            if not undecided.has_opt(loc, Cells.DECIDED_EMPTY):
                return False
        elif not cell == Cells.DECIDED_EMPTY:
            return False

    return True

def deduce_consequences_empty(board: Board, undecided: Undecided, loc: Loc) -> bool:
    connected_decided_empty = get_connected_satisfying_condition(board, loc, lambda cell: cell == Cells.DECIDED_EMPTY)
    
    axis_closure = axis_rectangle_closure(connected_decided_empty)
    diagonal_closure = diagonal_rectangle_closure(connected_decided_empty)
    minimum_closure = axis_closure.intersection(diagonal_closure)

    for loc in minimum_closure:
        # all cells in the closure must be empty
        cell = board[loc]
        
        if cell == Cells.UNDECIDED:
            if not undecided.keep_opts(loc, Cells.DECIDED_EMPTY):
                return False
        elif not cell == Cells.DECIDED_EMPTY:
            return False
        
    return True