from __future__ import annotations

from typing import Tuple

Tube = Tuple[str, ...]          # bottom -> top
State = Tuple[Tube, ...]
Move = Tuple[int, int]          # (from_tube, to_tube)

CAPACITY = 4
PRINT_EVERY = 100_000
MAX_NODES = 30_000_000
