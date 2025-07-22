from __future__ import annotations
from package.Cell import Cell, Cells
from package.util import SURROUNDING_DELTAS
from package.Loc import Loc
from package.Board import Board
from package.Undecided import Undecided, all_opts_undecided
from package.SolutionValidator import SolutionValidator
from package.empty_logic import deduce_consequences_empty, is_empty_still_possible
from package.triangle_logic import deduce_consequences_triangle, is_triangle_still_possible
from package.number_logic import update_opts_around_number
from typing import Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import os

class Solver:
    """
    A class to encapsulate the Shakashaka puzzle solving process.
    Maintains board and undecided state internally to avoid passing them around.
    """
    
    def __init__(self, board: Board, undecided: Undecided | None = None):
        self.board = board
        if undecided:
            self.undecided = undecided
        else:
            self.undecided = all_opts_undecided(board)
            self._initial_prune()
            
    def _initial_prune(self) -> None:
        """
        Perform initial prune of options
        """
        for loc, opts in self.undecided:
            for opt in opts:
                if opt in Cells.TRIANGLES:
                    if not is_triangle_still_possible(self.board, self.undecided, loc, opt):
                        self.undecided.remove_opts(loc, opt)
                else:
                    # opt == Cells.DECIDED_EMPTY
                    if not is_empty_still_possible(self.board, self.undecided, loc):
                        self.undecided.remove_opts(loc, opt)
                        
        for loc, cell in self.board:
            if cell.is_number:
                if not update_opts_around_number(self.board, self.undecided, loc, cell):
                    raise ValueError(f"Invalid board state: {loc} with {cell} cannot be satisfied")
            
    def copy(self) -> Solver:
        """
        Create a copy of the solver with the current board and undecided state.
        """
        return Solver(self.board.copy(), self.undecided.copy())

    def solve(self) -> list[Board]:
        """Solve the puzzle and return all possible solutions."""
        if not self.undecided:
            return [self.board] if self._is_solved() else []

        solutions = []

        loc, opts = self.undecided.get_undecided_with_minimal_opts()
        
        if len(opts) == 1:
            if self.make_assignment(loc, next(iter(opts))):
                return self.solve()
            return []
        
        # Use multithreading for multiple options with thread limit management
        # The current thread will also do work, so we include it in the distribution
        def try_option(cell: Cell) -> list[Board]:
            """Try a single option and return solutions."""
            solver = self.copy()
            if solver.make_assignment(loc, cell):
                return solver.solve()
            return []
        
        def try_multiple_options(cells: list[Cell]) -> list[Board]:
            """Try multiple options sequentially in a single thread."""
            thread_solutions = []
            for cell in cells:
                try:
                    cell_solutions = try_option(cell)
                    thread_solutions.extend(cell_solutions)
                except Exception as e:
                    print(f"Error trying option {cell} at {loc}: {e}")
            return thread_solutions
        
        # Calculate available threads (child threads only)
        max_total_threads = min((os.cpu_count() or 4), 100)
        current_active_threads = threading.active_count()
        
        max_child_threads = max(0, max_total_threads - current_active_threads)
        max_child_threads = min(max_child_threads, len(opts) - 1) # don't need more child threads than opts - 1
        
        opts_list = list(opts)
        
        # Total workers = child threads + current thread
        total_workers = max_child_threads + 1
        
        # Distribute options among all workers (including current thread)
        options_per_worker = len(opts_list) // total_workers
        remainder = len(opts_list) % total_workers
        
        worker_assignments = []
        start_idx = 0
        
        for i in range(total_workers):
            # Give extra option to first 'remainder' workers
            worker_size = options_per_worker + (1 if i < remainder else 0)
            end_idx = start_idx + worker_size
            worker_assignments.append(opts_list[start_idx:end_idx])
            start_idx = end_idx
        
        # Reserve the last assignment for the current thread
        current_thread_assignment = worker_assignments.pop()
        child_thread_assignments = worker_assignments
        
        # Launch child threads first (before mutating current state)
        if child_thread_assignments and max_child_threads > 0:
            with ThreadPoolExecutor(max_workers=max_child_threads) as executor:
                # Submit child thread work
                future_to_assignment = {
                    executor.submit(try_multiple_options, assignment): assignment 
                    for assignment in child_thread_assignments
                }
                
                # Current thread does its share of work while children work
                current_thread_solutions = try_multiple_options(current_thread_assignment)
                solutions.extend(current_thread_solutions)
                
                # Collect results from child threads
                for future in as_completed(future_to_assignment):
                    try:
                        new_solutions = future.result()
                        solutions.extend(new_solutions)
                    except Exception as e:
                        assignment = future_to_assignment[future]
                        print(f"Error trying options {assignment} at {loc}: {e}")
        else:
            # No child threads possible, current thread does all work
            current_thread_solutions = try_multiple_options(current_thread_assignment)
            solutions.extend(current_thread_solutions)

        return solutions

    def _is_solved(self) -> bool:
        """Check if the current board state is a valid solution."""
        return SolutionValidator(self.board).validate()

    def make_assignment(self, loc: Loc, cell: Cell) -> bool:
        """Update options after placing a cell, return False if contradiction found."""
        self.board[loc] = cell
        self.undecided.remove_loc(loc)
        
        try:
            if not self._deduce_consequences(loc, cell):
                return False
            
            if not self._update_surrounding_opts(loc, cell):
                return False
        except ValueError as e:
            print(f"Error during assignment of {loc} with {cell}: {e}")
            print(self.board)
            raise e
        
        # print(self.board)
        # print(self.undecided)
        
        return True

    def _deduce_consequences(self, loc: Loc, cell: Cell) -> bool:
        """Deduce logical consequences of placing a cell at the given location."""
        if cell == Cells.DECIDED_EMPTY:
            return deduce_consequences_empty(self.board, self.undecided, loc)
        elif cell.is_triangle:
            return deduce_consequences_triangle(self.board, self.undecided, loc)
        
        raise ValueError("Nonempty and nontriangle cell option")

    def _update_surrounding_opts(self, loc: Loc, cell: Cell) -> bool:
        """Update the possibilities of surrounding cells based on the new cell."""
        for delta in SURROUNDING_DELTAS:
            neighbor_loc = loc + delta
            if self.board[neighbor_loc] == Cells.UNDECIDED:
                neighbor_opts = self.undecided.get_opts(neighbor_loc)
                to_remove = {opt for opt in neighbor_opts if not self._is_opt_still_possible(neighbor_loc, opt)}
                
                neighbor_has_opts_left = self.undecided.remove_opts(neighbor_loc, to_remove)
                
                if not neighbor_has_opts_left:
                    return False
            elif self.board[neighbor_loc].is_number:
                if not update_opts_around_number(self.board, self.undecided, neighbor_loc, self.board[neighbor_loc]):
                    return False
        return True

    def _is_opt_still_possible(self, loc: Loc, opt: Cell) -> bool:
        """Check if the given cell is a possible option for the given location."""
        if opt == Cells.DECIDED_EMPTY:
            return is_empty_still_possible(self.board, self.undecided, loc)
        elif opt.is_triangle:
            return is_triangle_still_possible(self.board, self.undecided, loc, opt)
        
        raise ValueError("Nonempty and nontriangle cell option")