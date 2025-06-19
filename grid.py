"""Grid module – returns Optional[Cell] for safe typing."""
from __future__ import annotations
from typing import Optional, Tuple
import config
from cell import Cell

class Grid:
    def __init__(self, width: Optional[int] = None, height: Optional[int] = None):
        """Initialize the grid with given width/height or default config values."""
        self.width = width if width is not None else config.GRID_WIDTH
        self.height = height if height is not None else config.GRID_HEIGHT
        # Build 2‑D cell matrix
        self.cells: list[list[Cell]] = []
        for x in range(self.width):
            col: list[Cell] = []
            for y in range(self.height):
                # Cell type rules
                if x == 0 and y < config.INBOUND_CELLS:
                    ctype = "inbound"
                elif x == self.width - 1 and y < config.OUTBOUND_CELLS:
                    ctype = "outbound"
                else:
                    ctype = "storage"
                col.append(Cell(x, y, ctype))
            self.cells.append(col)

    # ------------------------------------------------------------------
    def get_cell(self, x: int, y: int) -> Optional[Cell]:
        """Return cell at (x,y) or None if out of bounds."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.cells[x][y]
        return None

    def find_empty_storage_cell(self, exclude: Optional[set[Cell]] = None) -> Optional[Cell]:
        """Return a random storage cell with spare capacity, excluding any provided."""
        import random
        if exclude is None:
            exclude = set()
        candidates: list[Cell] = []
        for col in self.cells:
            for cell in col:
                if cell.type == "storage" and len(cell.items) < config.MAX_ITEMS_PER_CELL and cell not in exclude:
                    candidates.append(cell)
        return random.choice(candidates) if candidates else None

    def find_item(self, code: str) -> Tuple[Optional[Cell], Optional[object]]:
        """Locate an item by code; search storage+inbound."""
        for col in self.cells:
            for cell in col:
                if cell.type in ("storage", "inbound"):
                    for item in cell.items:
                        if item.code == code:
                            return cell, item
        return None, None
