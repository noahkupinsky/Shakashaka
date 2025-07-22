from package.Board import Board
from package.Cell import Cell, Cells
from package.Loc import Loc
from typing import Callable, Dict

SURROUNDING_DELTAS = [
    Loc(-1, -1), Loc(0, -1), Loc(1, -1),
    Loc(-1, 0), Loc(1, 0),
    Loc(-1, 1), Loc(0, 1), Loc(1, 1)
]

AXIS_NEIGHBORS = [
    Loc(-1, 0), Loc(1, 0), Loc(0, -1), Loc(0, 1)
]

