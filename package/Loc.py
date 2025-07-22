from __future__ import annotations
from typing import Tuple, Iterator


type Numeric = int | float
type LocLike = Loc | Tuple[Numeric, Numeric]

def assert_loc_like(value: any) -> bool:
    """Check if the value is a Loc or a tuple of two integers."""
    if isinstance(value, Loc):
        return True
    if isinstance(value, tuple) and len(value) == 2:
        return True
    raise TypeError(f"Invalid LocLike value: {value}")

class Loc:
    def __init__(self, x: Numeric, y: Numeric):
        self.x = x
        self.y = y
        
    def is_integral(self) -> bool:
        """Check if both coordinates are integer"""
        return self.x == int(self.x) and self.y == int(self.y)

    def __iter__(self) -> Iterator[Numeric]:
        """Allow destructuring: x, y = my_loc"""
        yield self.x
        yield self.y

    def __getitem__(self, index: int) -> Numeric:
        """Allow indexing: my_loc[0] or my_loc[1]. Lets all LocLikes be treated similarly"""
        if not isinstance(index, int) or index < 0 or index > 1:
            raise TypeError("Supported indices on type Loc are 0 and 1")

        if index == 0:
            return self.x
        elif index == 1:
            return self.y
        
    def __add__(self, other: LocLike) -> Loc:
        """Addition: loc1 + loc2"""
        assert_loc_like(other)
        other_x, other_y = other
        return Loc(self.x + other_x, self.y + other_y)

    def __sub__(self, other: LocLike) -> Loc:
        """Subtraction: loc1 - loc2"""
        assert_loc_like(other)
        other_x, other_y = other
        return Loc(self.x - other_x, self.y - other_y)

    def __mul__(self, scalar: int | float) -> Loc:
        """Scalar multiplication: loc * scalar"""
        if isinstance(scalar, (int, float)):
            return Loc(self.x * scalar, self.y * scalar)
        raise TypeError("Cannot multiply Loc with non-numeric type")
    
    def __neg__(self) -> Loc:
        """Negation: -loc"""
        return Loc(-self.x, -self.y)
    
    def __truediv__(self, scalar: int | float) -> Loc:
        """Scalar division: loc / scalar"""
        if isinstance(scalar, (int, float)) and scalar != 0:
            return Loc(self.x / scalar, self.y / scalar)
        raise ValueError("Cannot divide Loc by zero or non-numeric type")
    
    def __rmul__(self, scalar: int | float) -> Loc:
        """Right scalar multiplication: scalar * loc"""
        return self.__mul__(scalar)

    def __eq__(self, other) -> bool:
        """Equality comparison"""
        try:
            other_x, other_y = other
            return self.x == other_x and self.y == other_y
        except (ValueError, TypeError):
            return False
    
    def __hash__(self):
        """Make Loc hashable for use in sets/dicts"""
        return hash((self.x, self.y))
    
    def __repr__(self):
        return f"Loc({self.x}, {self.y})"
    
    def __str__(self):
        return f"({self.x}, {self.y})"