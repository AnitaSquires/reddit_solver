class PuzzleButton:
    """Wrapper around a ColumnContainer"""

    def __init__(self, column):
        self.column = column

    def _refresh(self, slot_index):
        token = self.column.slot_tokens[slot_index]
        rgb = self.column.slot_rgbs[slot_index]
        return token, rgb

    @property
    def slot_one(self):
        return self._refresh(0)

    @property
    def slot_two(self):
        return self._refresh(1)

    @property
    def slot_three(self):
        return self._refresh(2)

    @property
    def slot_four(self):
        return self._refresh(3)

    @property
    def tube(self):
        return tuple(
            t for t in reversed(self.column.slot_tokens) if t is not None
        )