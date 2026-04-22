from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np

RGB = Tuple[int, int, int]
Tube = Tuple[str, ...]
State = Tuple[Tube, ...]

CAPACITY = 4
SAMPLE_Y_FRACS = [0.18, 0.43, 0.67, 0.90]


@dataclass
class ColumnContainer:
    """
    One puzzle tube/column with 4 vertical slots.
    """
    index: int
    row: int
    col: int
    forced_empty: bool = False
    slot_rgbs: List[Optional[RGB]] = field(default_factory=lambda: [None] * CAPACITY)
    slot_tokens: List[Optional[str]] = field(default_factory=lambda: [None] * CAPACITY)

    def set_rgb(self, slot_index: int, rgb: Optional[RGB]) -> None:
        self.slot_rgbs[slot_index] = rgb

    def set_token(self, slot_index: int, token: Optional[str]) -> None:
        self.slot_tokens[slot_index] = token

    def clear(self) -> None:
        for i in range(CAPACITY):
            self.slot_rgbs[i] = None
            self.slot_tokens[i] = None

    def as_tube(self) -> Tube:
        if self.forced_empty:
            return ()

        filled = [token for token in self.slot_tokens if token is not None]
        return tuple(reversed(filled)) if filled else ()


@dataclass
class BoardModel:
    """
    Holds the full board as column-first tube objects.
    The last `forced_empty_columns` columns are always empty.
    """
    rows: int
    cols: int
    forced_empty_columns: int = 2
    columns: List[ColumnContainer] = field(init=False)

    def __post_init__(self) -> None:
        self.columns = [
            ColumnContainer(
                index=col * self.rows + row,
                row=row,
                col=col,
                forced_empty=(col >= self.cols - self.forced_empty_columns),
            )
            for col in range(self.cols)
            for row in range(self.rows)
        ]

    def update_board(self, img: np.ndarray, sampler) -> None:
        """
        Sample each tube/column in column-major order.

        `sampler` must have the signature:
            sampler(img, x, y) -> (r, g, b)
        """
        h, w, _ = img.shape

        grid_left, grid_right = 0.05, 0.95
        grid_top, grid_bottom = 0.12, 0.83

        cell_w = (grid_right - grid_left) * w / self.cols
        cell_h = (grid_bottom - grid_top) * h / self.rows
        start_x = grid_left * w
        start_y = grid_top * h

        for column in self.columns:
            if column.forced_empty:
                column.clear()
                continue

            cell_x = start_x + column.col * cell_w
            cell_y = start_y + column.row * cell_h
            cx = int(round(cell_x + cell_w * 0.50))

            for slot_index, frac in enumerate(SAMPLE_Y_FRACS):
                cy = int(round(cell_y + cell_h * frac))
                rgb = sampler(img, cx, cy)
                column.set_rgb(slot_index, rgb)

    def to_state(self) -> State:
        return tuple(column.as_tube() for column in self.columns)