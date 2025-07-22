from __future__ import annotations
from typing import Dict, Set, List, Iterable, Callable
from package.Cell import Cell, Cells
from package.Loc import Loc
from package.Board import Board

class Undecided:
    """
    Stores all cells that are undecided, and their possible values
    """
    def __init__(self, opts: Dict[Loc, set[Cell]], num_opt_sets: List[Set[Loc]] | None = None):
        self.opts = opts
        
        if num_opt_sets is not None:
            self.num_opt_sets = num_opt_sets
        else:
            self.num_opt_sets: List[Set[Loc]] = [set() for _ in range(6)]
            
            for loc, cells in opts.items():
                self.num_opt_sets[len(cells)].add(loc)
                
    def __bool__(self) -> bool:
        """
        Returns True if there are any undecided cells left
        """
        return bool(self.opts)
                
    def remove_loc(self, loc: Loc) -> None:
        """
        Remove the given location from the undecided cells
        """
        if loc not in self.opts:
            raise ValueError(f"Cannot remove {loc} as it is not in undecided")
        
        num_opts = len(self.opts[loc])
        del self.opts[loc]
        
        self.num_opt_sets[num_opts].discard(loc)
                
    def has_opt(self, loc: Loc, cell: Cell) -> bool:
        """
        Check if the given cell is a possible option for the given location
        """
        if loc not in self.opts:
            raise ValueError(f"Cannot check opts for {loc} as it is not in undecided")
        return cell in self.opts[loc]
                
    def get_opts(self, loc: Loc) -> set[Cell]:
        """
        Get the options for the given location
        """
        if loc not in self.opts:
            raise ValueError(f"Cannot get opts for {loc} as it is not in undecided")
        return self.opts[loc]

    def remove_opts(self, loc: Loc, cells: Cell | Iterable[Cell]) -> bool:
        """
        Remove the give cell(s) from the options for the given location
        returns True if the cell still has options left
        """
        if loc not in self.opts:
            raise ValueError(f"Cannot remove opts for {loc} as it is not in undecided")
        
        if isinstance(cells, Cell):
            cells = [cells]
        cells = set(cells)
        filter = lambda cell: cell not in cells
        return self._filter_opts(loc, filter)
    
    def keep_opts(self, loc: Loc, cells: Cell | Iterable[Cell]) -> bool:
        """
        Removes all options except the given cell(s) from the given location
        returns True if the cell still has options left
        """
        if isinstance(cells, Cell):
            cells = [cells]
        cells = set(cells)
        filter = lambda cell: cell in cells
        return self._filter_opts(loc, filter)

    def _filter_opts(self, loc: Loc, filter: Callable[[Cell], bool]) -> bool:
        """
        Removes all options that do not satisfy the given filter from the given location
        returns True if the cell still has options left
        """
        if loc not in self.opts:
            raise ValueError(f"Cannot filter opts for {loc} as it is not in undecided")

        prev_num_opts = len(self.opts.get(loc))

        self.opts[loc] = {cell for cell in self.opts[loc] if filter(cell)}

        new_num_opts = len(self.opts.get(loc))

        self.num_opt_sets[prev_num_opts].discard(loc)
        self.num_opt_sets[new_num_opts].add(loc)

        return new_num_opts > 0
    
    def get_undecided_with_minimal_opts(self) -> tuple[Loc, set[Cell]]:
        """
        returns any undecided cell with minimal options
        """
        if not self.opts:
            raise ValueError("No undecided cells left")
        
        min_num_opts = 5
        for i in range(6):
            if self.num_opt_sets[i]:
                min_num_opts = i
                break
            
        if min_num_opts == 0:
            raise ValueError("Called next on a board state containing a cell with no options left.")
        
        # return any loc with min_num_opts
        loc = next(iter(self.num_opt_sets[min_num_opts]))
        return loc, self.opts[loc]
    
    def __iter__(self) -> Iterable[Loc]:
        return iter(self.opts.items())

    def copy(self) -> Undecided:
        opts_copy = {loc: cells.copy() for loc, cells in self.opts.items()}
        num_opt_sets_copy = [s.copy() for s in self.num_opt_sets]
        return Undecided(opts_copy, num_opt_sets=num_opt_sets_copy)
    
    def __str__(self):
        loc_strings = []
        for loc_list in self.num_opt_sets:
            for loc in loc_list:
                cells = self.opts[loc]
                cell_str = ", ".join(str(cell) for cell in cells)
                loc_strings.append(f"{loc}: {cell_str}")
        return "\n".join(loc_strings)

def all_opts_undecided(board: Board) -> Undecided:
    opts = {}
    for loc, cell in board:
        if cell == Cells.UNDECIDED:
            opts[loc] = Cells.OPTIONS.copy()
    return Undecided(opts)