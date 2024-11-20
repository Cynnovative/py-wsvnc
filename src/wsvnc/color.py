"""RGB Color class object."""

from dataclasses import dataclass


@dataclass
class Color:
    r: int
    g: int
    b: int
