from __future__ import annotations
    
class Cell:
    def __init__(self, char: str, 
                 is_triangle: bool = False,
                 is_undecided_or_empty: bool = False, 
                 number: int | None = None):
        self.char = char
        self.number = number
        self.is_triangle = is_triangle
        self.is_undecided_or_empty = is_undecided_or_empty
        self.is_number = number is not None

    def __str__(self) -> str:
        return self.char
    
    def __repr__(self) -> str:
        return f"Cell({self.char})"

    def __eq__(self, value: Cell) -> bool:
        if isinstance(value, Cell):
            return self.char == value.char
        return False

    def __hash__(self) -> int:
        return hash(self.char)

class Cells:
    ZERO = Cell('0', number = 0)
    ONE = Cell('1', number = 1)
    TWO = Cell('2', number = 2)
    THREE = Cell('3', number = 3)
    FOUR = Cell('4', number = 4)
    BLACK = Cell('■')
    UNDECIDED = Cell(' ', is_undecided_or_empty=True)
    DECIDED_EMPTY = Cell('◦', is_undecided_or_empty=True)
    LOWER_LEFT = Cell('◣', is_triangle=True)
    LOWER_RIGHT = Cell('◢', is_triangle=True)
    UPPER_LEFT = Cell('◤', is_triangle=True)
    UPPER_RIGHT = Cell('◥', is_triangle=True)
    
    TRIANGLES = {LOWER_LEFT, LOWER_RIGHT, UPPER_LEFT, UPPER_RIGHT}
    OPTIONS = {DECIDED_EMPTY, *TRIANGLES}
    ALL = {ZERO, ONE, TWO, THREE, FOUR, BLACK, UNDECIDED, DECIDED_EMPTY, LOWER_LEFT, LOWER_RIGHT, UPPER_LEFT, UPPER_RIGHT}

