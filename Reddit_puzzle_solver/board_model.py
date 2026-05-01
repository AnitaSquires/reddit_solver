from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np

RGB = Tuple[int, int, int]
Tube = Tuple[str, ...]
State = Tuple[Tube, ...]

CAPACITY = 4

# Slightly tighter vertical sampling (more centered)
SAMPLE_Y_FRACS = [0.15, 0.38, 0.62, 0.85]


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

        # 🔥 FIXED GRID — tuned to your actual screenshots
        grid_left, grid_right = 0.12, 0.88
        grid_top, grid_bottom = 0.15, 0.85

        usable_w = (grid_right - grid_left) * w
        usable_h = (grid_bottom - grid_top) * h

        spacing_x = usable_w / (self.cols - 1)
        spacing_y = usable_h / (self.rows - 1)

        start_x = grid_left * w
        start_y = grid_top * h

        # approximate tube height (for slot spacing)
        tube_height = spacing_y * 0.8

        for column in self.columns:
            if column.forced_empty:
                column.clear()
                continue

            # 🔥 correct tube center positions
            cx = int(round(start_x + column.col * spacing_x))
            cy_base = int(round(start_y + column.row * spacing_y))

            # sample 4 slots inside tube
            for slot_index, frac in enumerate(SAMPLE_Y_FRACS):
                cy = int(round(cy_base + (frac - 0.5) * tube_height))

                # clamp for safety
                cy = max(0, min(h - 1, cy))

                rgb = sampler(img, cx, cy)
                column.set_rgb(slot_index, rgb)

    def to_state(self) -> State:
        return tuple(column.as_tube() for column in self.columns)