# cell.py

import config
from item import Item
from typing import Optional

class Cell:
    def __init__(self, x: int, y: int, cell_type: str = "storage"):
        """Initialize a cell at grid position (x, y). Type is 'storage', 'inbound', or 'outbound'."""
        self.x = x
        self.y = y
        self.type = cell_type
        # Use a list to represent the stack of items in this cell (index 0 is the *top* of stack for convenience)
        self.items = []
    
    def add_item(self, item: Item) -> bool:
        """Add an item to this cell's stack. Returns True if successful, False if cell is full (for storage)."""
        if self.type == "storage":
            if len(self.items) >= config.MAX_ITEMS_PER_CELL:
                return False  # cannot add, storage cell at capacity
        # Inbound/outbound cells we will not enforce a strict capacity in this simulation (or treat similarly to storage if desired).
        self.items.insert(0, item)  # push item on top of stack (at index 0)
        return True
    
    def remove_item(self) -> Optional[Item]:
        """Remove and return the top item from this cell (if any)."""
        if not self.items:
            return None
        return self.items.pop(0)  # pop from top of stack
    
    def peek_top(self) -> Optional[Item]:
        """Return the top item without removing it (or None if empty)."""
        return self.items[0] if self.items else None
    
    def needs_resort(self) -> bool:
        """Check if this cell's stack is out-of-order by preference (i.e., a higher-preference item is below a lower-preference item)."""
        # We need to detect if items are not in descending preference order from top to bottom.
        # If any item has a preference higher than one above it, then sorting is needed.
        for i in range(len(self.items) - 1):
            top_item = self.items[i]
            below_item = self.items[i+1]
            if top_item.preference < below_item.preference:
                # A lower preference item is above a higher preference item – needs resort
                return True
        return False
    
    def sort_items_by_preference(self):
        """Sort the stack so that items are in descending order of preference (top = highest preference)."""
        self.items.sort(key=lambda it: it.preference, reverse=True)
    
    def get_top_items(self, n: int):
        """Get the top n highest-preference items in this cell (for UI display)."""
        if not self.items:
            return []
        # If the cell is already sorted in descending order by preference, then the first n items are the highest.
        sorted_by_pref = sorted(self.items, key=lambda it: it.preference, reverse=True)
        return sorted_by_pref[:n]
    
    def get_bottom_items(self, n: int):
        """Get the bottom n lowest-preference items in this cell (for UI display)."""
        if not self.items:
            return []
        sorted_by_pref = sorted(self.items, key=lambda it: it.preference, reverse=True)
        if len(sorted_by_pref) <= n:
            lowest = sorted_by_pref[:]  # all items (in descending order)
        else:
            lowest = sorted_by_pref[-n:]  # last n in descending order (which are the lowest preference)
        lowest.sort(key=lambda it: it.preference)  # sort ascending for easier interpretation
        return lowest
