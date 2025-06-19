# item.py

import random
import config
from typing import Optional
class Item:
    def __init__(self, code: str, preference: Optional[float] = None):
        """Create an item with a unique code and an initial preference score."""
        self.code = code
        if preference is not None:
            # If a specific initial preference is provided, use it
            self.preference = preference
        else:
            # Initialize preference by pseudo-randomly deriving from the code
            # Use the item code to generate a seed so that each code yields a consistent random value
            try:
                seed_val = int(code, 36)  # interpret code as base-36 number for a deterministic seed
            except ValueError:
                seed_val = sum(ord(c) for c in code)
            rng = random.Random(seed_val)
            self.preference = rng.randint(1, 100)  # initial preference between 1 and 100 (inclusive)
    
    def update_preference(self):
        """Evolve the preference score (simulate changing item desirability over time)."""
        # For simplicity, adjust preference by a small random delta up or down, within [1,100] bounds
        delta = random.randint(-5, 5)
        new_pref = self.preference + delta
        # Clamp the value between 1 and 100
        if new_pref < 1:
            new_pref = 1
        if new_pref > 100:
            new_pref = 100
        self.preference = new_pref
