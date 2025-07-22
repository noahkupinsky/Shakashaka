from package.Board import Board, undecided_board
from package.Cell import Cell, Cells
from package.Loc import Loc
from package.Undecided import Undecided
from typing import List, Set, Tuple, Dict
from enum import Enum
from itertools import product

CHUNK_DELTA_TO_TRIANGLE: Dict[Loc, Cell] = {
    Loc(-0.5, -0.5): Cells.LOWER_LEFT,
    Loc(-0.5, 0.5): Cells.UPPER_LEFT,
    Loc(0.5, -0.5): Cells.LOWER_RIGHT,
    Loc(0.5, 0.5): Cells.UPPER_RIGHT
}

CHUNK_DELTAS_CLOCKWISE = [Loc(-0.5, -0.5), Loc(-0.5, 0.5), Loc(0.5, 0.5), Loc(0.5, -0.5)]

TRIANGLES_CLOCKWISE = [CHUNK_DELTA_TO_TRIANGLE[delta] for delta in CHUNK_DELTAS_CLOCKWISE]

TRIANGLE_TO_CHUNK_DELTA: Dict[Cell, Loc] = {v: k for k, v in CHUNK_DELTA_TO_TRIANGLE.items()}

def sort_pair(a: Loc, b: Loc) -> Tuple[Loc, Loc]:
    """Sort two locations by their coordinates."""
    if a.x < b.x or (a.x == b.x and a.y < b.y):
        return a, b
    return b, a

class Rotation(Enum):
    CLOCKWISE = 'clockwise'
    COUNTER_CLOCKWISE = 'counter_clockwise'

def rotate_index(i, rotation: Rotation) -> int:
    if rotation == Rotation.CLOCKWISE:
        return (i + 1) % 4
    else:
        return (i - 1) % 4
    
def get_turn_and_continue_data(rot: Rotation, dir_index: int, current: Loc) -> Tuple[List[Loc], List[Cell]]:
    rot_index = rotate_index(dir_index, rot)
    turn_triangle = TRIANGLES_CLOCKWISE[rot_index]
    turn_loc = current + -CHUNK_DELTAS_CLOCKWISE[dir_index] + CHUNK_DELTAS_CLOCKWISE[rot_index]
    continue_loc = current + 2 * CHUNK_DELTAS_CLOCKWISE[rot_index]
    
    return turn_loc, turn_triangle, continue_loc

class DiagonalRectangleValidator:
    def __init__(self, board: Board):
        self.board = board
        self.validated_chunks: Set[Loc] = set()
        self.validated_locs: Set[Loc] = set()

    def validate(self, initial_loc: Loc) -> bool:
        if not self._validate_initial_triangle(initial_loc):
            return False
        
        initial_chunk = self._get_initial_chunk(initial_loc)

        if not self._validate_chunks_cells_rec(initial_chunk):
            return False
        
        if not self._validate_chunks_form_diagonal_rectangle():
            return False

        return True
        

    def _validate_initial_triangle(self, initial_loc: Loc) -> bool:
        """Validate the initial triangle cell"""
        triangle_cell = self.board[initial_loc]
        
        if not triangle_cell.is_triangle:
            return False
        
        self.validated_locs.add(initial_loc)
        return True

    def _get_initial_chunk(self, initial_loc: Loc) -> Loc:
        """Get the initial chunk based on the initial triangle cell."""
        triangle_cell = self.board[initial_loc]
        initial_chunk_delta = TRIANGLE_TO_CHUNK_DELTA[triangle_cell]
        # this means that initial_loc = initial_chunk + initial_chunk_delta
        return initial_loc - initial_chunk_delta

    def _validate_chunks_cells_rec(self, chunk: Loc) -> bool:
        """Check if chunk is valid, i.e. all cells are either empty or the expected triangle."""
        if chunk in self.validated_chunks:
            return True

        for delta, expected_triangle in CHUNK_DELTA_TO_TRIANGLE.items():
            loc = chunk + delta
            if loc in self.validated_locs:
                continue
            cell = self.board[loc]

            if cell != expected_triangle and not cell.is_undecided_or_empty:
                return False
            
            self.validated_locs.add(loc)

            if cell.is_undecided_or_empty:
                # if the cell is empty, we have another chunk to validate. 
                # We move in the direction of the delta to the next chunk-grid point
                # chunks are always a + 0.5, b + 0.5 for some a, b, so the next one is at chunk + 2 * delta
                if not self._validate_chunks_cells_rec(chunk + 2 * delta):
                    return False

        self.validated_chunks.add(chunk)
        return True
    
    def _validate_chunks_form_diagonal_rectangle(self) -> bool:
        """Check if the validated chunks form a diagonal rectangle."""
        left = Loc(float('inf'), 0)
        top = Loc(0, float('-inf'))
        bottom = Loc(0, float('inf'))

        for loc in self.validated_chunks:
            if loc.x < left.x:
                left = loc
            if loc.y < bottom.y:
                bottom = loc
            if loc.y > top.y:
                top = loc

        up_right_steps = int((top - left).y)
        down_right_steps = int(-(bottom - left).y)

        expected_locs = {
            left + Loc(1, 1) * up_right + Loc(1, -1) * down_right 
            for up_right, down_right in product(range(up_right_steps + 1), range(down_right_steps + 1))
        }

        return expected_locs == self.validated_chunks

class PartialDiagonalRectangle:
    def __init__(self, board: Board):
        self.board = board
        self.visited = set()
        self.sides: List[List[Loc]] = []
        self.unfinished_ends = set()
        
    def _toggle_in_unfinished_ends(self, loc: Loc):
        """Toggle the presence of a location in the unfinished ends set."""
        if (loc, self.board[loc]) in self.unfinished_ends:
            self.unfinished_ends.remove((loc, self.board[loc]))
        else:
            self.unfinished_ends.add((loc, self.board[loc]))

    def on_undecided_board(self):
        """Visualize the partial diagonal rectangle."""
        b = undecided_board(self.board.size)
        for i, side in enumerate(self.sides):
            for loc in side:
                b[loc] = TRIANGLES_CLOCKWISE[i]
        return b

    def __str__(self):
        return str(self.on_undecided_board())

    def construct_from_starting_loc(self, start_loc: Loc) -> bool:
        """
        Find all triangles connected to the starting triangle in a diagonal rectangle.
        returns False if the PDR splits illegally, true otherwise
        """

        self.visited = set()
        to_visit = [start_loc]
        
        loc_pairs_map: Dict[Tuple[Loc, Loc], List[Loc]] = {}
        
        while to_visit:
            current = to_visit.pop()
            if current in self.visited:
                continue

            self.visited.add(current)
            loc_pairs = []
            
            triangle = self.board[current]
            dir_index = TRIANGLES_CLOCKWISE.index(triangle)

            for rot in [Rotation.CLOCKWISE, Rotation.COUNTER_CLOCKWISE]:
                turn_loc, turn_triangle, continue_loc = get_turn_and_continue_data(rot, dir_index, current)

                paths = 0
                for path_loc, path_triangle in [
                    (turn_loc, turn_triangle),
                    (continue_loc, triangle)
                ]:
                    if self.board[path_loc] == path_triangle:
                        to_visit.append(path_loc)
                        loc_pairs.append(sort_pair(current, path_loc))
                        paths += 1
                    
                if paths > 1:
                    return False
            
            for loc_pair in loc_pairs:
                if loc_pair not in loc_pairs_map:
                    loc_pairs_map[loc_pair] = [current]
                elif len(loc_pairs_map[loc_pair]) == 1:
                    already_in_pair = loc_pairs_map[loc_pair][0]
                    if already_in_pair != current:
                        loc_pairs_map[loc_pair].append(current)
                        self._toggle_in_unfinished_ends(already_in_pair)
                        self._toggle_in_unfinished_ends(current)

        if len(self.visited) == 1:
            self._toggle_in_unfinished_ends(start_loc)

        self.sides = [
            sorted(
                [loc for loc in self.visited if self.board[loc] == triangle_cell],
                key= lambda loc: loc.x, 
                reverse=(i == 0 or i == 3)
            )
            for i, triangle_cell in enumerate(TRIANGLES_CLOCKWISE)
        ]
        
        return True

    def _calculate_rectangle_dimensions(self) -> Tuple[int, int]:
        """Calculate the X and Y dimensions of the diagonal rectangle."""
        x_length = max(1, len(self.sides[1]), len(self.sides[3]))
        y_length = max(1, len(self.sides[0]), len(self.sides[2]))
        return x_length, y_length

    def _get_whitespace_side_endpoints(self) -> Tuple[List[Loc | None], List[Loc | None]]:
        """Get the start and end points of each whitespace side."""
        whitespace_side_starts = [
            None if not side else side[0] + Loc(0.5, 0.5) + CHUNK_DELTAS_CLOCKWISE[rotate_index(i, Rotation.COUNTER_CLOCKWISE)]
            for i, side in enumerate(self.sides)
        ]

        whitespace_side_ends = [
            None if not side else side[-1] + Loc(0.5, 0.5) + CHUNK_DELTAS_CLOCKWISE[rotate_index(i, Rotation.CLOCKWISE)]
            for i, side in enumerate(self.sides)
        ]
        
        return whitespace_side_starts, whitespace_side_ends

    def _find_corner_index(self, whitespace_side_starts: List[Loc | None], whitespace_side_ends: List[Loc | None]) -> int:
        """Find a corner index to use as reference for rectangle construction."""
        if len([side for side in self.sides if side]) == 1:
            # we only have one side, just find that side
            for i in range(4):
                if self.sides[i]:
                    return i
        else:
            # we have >= two sides, find any corner where two meet
            for i in range(4):
                current_side_end = whitespace_side_ends[i]
                next_side_start = whitespace_side_starts[rotate_index(i, Rotation.CLOCKWISE)]
                if current_side_end and next_side_start and current_side_end == next_side_start:
                    return i
                
        return None

    def _calculate_closure_corners(self, corner_index: int, found_corner: Loc, x_length: int, y_length: int) -> Tuple[List[Loc], List[Loc]]:
        """Calculate all corners of the closure rectangle."""
        first_corner_to_corner = [
            Loc(0, 0),
            Loc(1, 1) * x_length,
            Loc(1, 1) * x_length + Loc(1, -1) * y_length,
            Loc(1, -1) * y_length,
        ]

        first_corner = found_corner - first_corner_to_corner[corner_index]
        corners = [first_corner + first_corner_to_corner[i] for i in range(4)]
        # because corner i is at the end of side i, these are our END corners
        end_corners = corners
        start_corners = [corners[(i - 1) % 4] for i in range(4)]
        
        return start_corners, end_corners
    
    def _whitespace_corners_to_side(self, side_index: int, start_corner: Loc, end_corner: Loc) -> List[Loc]:
        difference = end_corner - start_corner
        # difference.x and difference.y will have the same abs value
        num_steps = int(abs(difference.x))
        step = difference / num_steps
        whitespace_side = [start_corner + step * i for i in range(num_steps)]

        # whitespace_side[0] = start_corner = side[0] + Loc(0.5, 0.5) + CHUNK_DELTAS_CLOCKWISE[rotate_index(side_index, Rotation.COUNTER_CLOCKWISE)]
        # side[i] = whitespace_side[i] - Loc(0.5, 0.5) - CHUNK_DELTAS_CLOCKWISE[rotate_index(side_index, Rotation.COUNTER_CLOCKWISE)]
        return [loc - Loc(0.5, 0.5) - CHUNK_DELTAS_CLOCKWISE[rotate_index(side_index, Rotation.COUNTER_CLOCKWISE)] for loc in whitespace_side]

    def _build_closure_sides(self, start_corners: List[Loc], end_corners: List[Loc]) -> List[List[Loc]]:
        """Build the complete sides of the closure rectangle."""
        return [
            self._whitespace_corners_to_side(i, start_corners[i], end_corners[i])
            for i in range(4)
        ]

    def _calculate_closure_interior(self, closure_sides: List[List[Loc]]) -> Set[Loc]:
        """Calculate all interior points of the closure rectangle."""
        closure_interior: Set[Loc] = set()
        
        bottom_to_top_left = closure_sides[0] + closure_sides[1]
        top_to_bottom_right = closure_sides[2] + closure_sides[3]
        height = len(bottom_to_top_left)  # == len(top_to_bottom_right)
        
        for i, left in enumerate(bottom_to_top_left):
            right = top_to_bottom_right[height - i - 1]
            y = int(left.y)
            for x in range(int(left.x) + 1, int(right.x)):
                closure_interior.add(Loc(x, y))
                
        return closure_interior

    def _build_closure_perimeter(self, closure_sides: List[List[Loc]]) -> Set[Tuple[Loc, Cell]]:
        """Build the perimeter of the closure rectangle with associated triangles."""
        closure_perimeter: Set[Tuple[Loc, Cell]] = set()
        
        for i, side in enumerate(closure_sides):
            side_triangle = TRIANGLES_CLOCKWISE[i]
            for loc in side:
                closure_perimeter.add((loc, side_triangle))
                
        return closure_perimeter

    def get_closure(self) -> Tuple[Set[Tuple[Loc, Cell]], Set[Loc]]:
        """
        Get the complete closure of the diagonal rectangle.
        Returns (perimeter_with_triangles, interior_locations).
        """
        x_length, y_length = self._calculate_rectangle_dimensions()
        whitespace_side_starts, whitespace_side_ends = self._get_whitespace_side_endpoints()
        corner_index = self._find_corner_index(whitespace_side_starts, whitespace_side_ends)
        
        found_corner = whitespace_side_ends[corner_index]

        start_corners, end_corners = self._calculate_closure_corners(corner_index, found_corner, x_length, y_length)
        closure_sides = self._build_closure_sides(start_corners, end_corners)
        
        closure_interior = self._calculate_closure_interior(closure_sides)
        closure_perimeter = self._build_closure_perimeter(closure_sides)
        
        return closure_perimeter, closure_interior
        

def deduce_consequences_triangle(board: Board, undecided: Undecided, loc: Loc) -> bool:
    pdr = PartialDiagonalRectangle(board)
    
    construction_successful = pdr.construct_from_starting_loc(loc)
    
    if not construction_successful:
        raise ValueError(f"Expected diagonal rectangle to be constructable from {loc}, but it is not.")
    
    closure_perimeter, closure_interior = pdr.get_closure()
    
    for loc, expected_triangle in closure_perimeter:
        cell = board[loc]
        # if the diag rect in the solution is bigger, we could have some decided cells on the perimeter that are empty
        if cell == Cells.UNDECIDED:
            if not undecided.keep_opts(loc, {expected_triangle, Cells.DECIDED_EMPTY}):
                return False
        elif not cell == expected_triangle and not cell == Cells.DECIDED_EMPTY:
            return False
            # raise ValueError(f"Expected decided cell at {loc} to be {expected_triangle} or empty, but found {cell}")
        
    for loc in closure_interior:
        cell = board[loc]
        if cell == Cells.UNDECIDED:
            if not undecided.keep_opts(loc, Cells.DECIDED_EMPTY):
                return False
        elif not cell == Cells.DECIDED_EMPTY:
            return False
            # raise ValueError(f"Expected decided cell at {loc} to be empty, but found {cell}")
    

    ends = pdr.unfinished_ends
    for end_loc, end_triangle in ends:
        dir_index = TRIANGLES_CLOCKWISE.index(end_triangle)
        for rot in [Rotation.CLOCKWISE, Rotation.COUNTER_CLOCKWISE]:
            turn_loc, turn_triangle, continue_loc = get_turn_and_continue_data(rot, dir_index, end_loc)
            
            if turn_loc in pdr.visited or continue_loc in pdr.visited:
                # this is not the direction the pdr ends at
                continue
            # we need one of turn_loc, continue_loc to be a triangle, and we know currently they are both not
            # if neither is undecided we can't finish this pdr
            if not board[turn_loc] == Cells.UNDECIDED and not board[continue_loc] == Cells.UNDECIDED:
                return False
            
            # if we know we can't turn, we have to continue
            if board[continue_loc] == Cells.UNDECIDED and not board[turn_loc] == Cells.UNDECIDED:
                if not undecided.keep_opts(continue_loc, end_triangle):
                    return False
            
            # if we know we can't continue, we have to turn
            if board[turn_loc] == Cells.UNDECIDED and not board[continue_loc] == Cells.UNDECIDED:
                if not undecided.keep_opts(turn_loc, turn_triangle):
                    return False

    return True

def is_triangle_still_possible(board: Board, undecided: Undecided, loc: Loc, cell: Cell) -> bool:
    pdr = PartialDiagonalRectangle(board)
    
    actual_cell_at_start_loc = board[loc]  # temporarily set the cell to check the closure
    board[loc] = cell  # temporarily set the cell to check the closure
    
    construction_successful = pdr.construct_from_starting_loc(loc)
    
    board[loc] = actual_cell_at_start_loc  # restore the original cell at start_loc
    
    if not construction_successful:
        return False
    
    closure_perimeter, closure_interior = pdr.get_closure()
    
    for loc, expected_triangle in closure_perimeter:
        cell = board[loc]
        # if the diag rect in the solution is bigger, we could have some decided cells on the perimeter that are empty
        if cell == Cells.UNDECIDED:
            if not undecided.has_opt(loc, expected_triangle) and not undecided.has_opt(loc, Cells.DECIDED_EMPTY):
                return False
        elif not cell == expected_triangle and not cell == Cells.DECIDED_EMPTY:
            return False
        
    for loc in closure_interior:
        cell = board[loc]
        if cell == Cells.UNDECIDED:
            if not undecided.has_opt(loc, Cells.DECIDED_EMPTY):
                return False
        elif not cell == Cells.DECIDED_EMPTY:
            return False
    
    ends = pdr.unfinished_ends
    for end_loc, end_triangle in ends:
        dir_index = TRIANGLES_CLOCKWISE.index(end_triangle)
        for rot in [Rotation.CLOCKWISE, Rotation.COUNTER_CLOCKWISE]:
            turn_loc, turn_triangle, continue_loc = get_turn_and_continue_data(rot, dir_index, end_loc)
            
            if turn_loc in pdr.visited or continue_loc in pdr.visited:
                # this is not the direction the pdr ends at
                continue
            # we need one of turn_loc, continue_loc to be a triangle, and we know currently they are both not
            # if neither is undecided we can't finish this pdr
            if not board[turn_loc] == Cells.UNDECIDED and not board[continue_loc] == Cells.UNDECIDED:
                return False
            
            # if we know we can't turn, we have to continue
            if board[continue_loc] == Cells.UNDECIDED and not board[turn_loc] == Cells.UNDECIDED:
                if not undecided.has_opt(continue_loc, end_triangle):
                    return False
            
            # if we know we can't continue, we have to turn
            if board[turn_loc] == Cells.UNDECIDED and not board[continue_loc] == Cells.UNDECIDED:
                if not undecided.has_opt(turn_loc, turn_triangle):
                    return False

    return True

def print_closure_perimeter(board_size, closure_perimeter: Set[Tuple[Loc, Cell]]):
    """Print the closure perimeter for debugging."""
    empty_grid = [
        [Cells.UNDECIDED for _ in range(board_size)] for _ in range(board_size)
    ]
    b = Board(empty_grid)
    for loc, cell in closure_perimeter:
        b[loc] = cell
    print(b)