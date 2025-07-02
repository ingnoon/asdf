# bot.py

import math
import config
# Bot._compute_path_to(...)
from pathfinder import find_path

from cell import Cell, Item

class Bot:
    def __init__(self, bot_id: str, start_cell: Cell, grid, *, color):
        """Initialize a Bot with an ID (e.g., 'a', 'b', 'c', ...) at a starting cell position."""
        self.bot_id = bot_id
        # Position in continuous (x, y) grid coordinates (not pixels, but in cell units for easier path calculations).
        self.pos = [start_cell.x, start_cell.y]  # using [x, y] float values
        self.grid = grid
        self.goal_coords = None  # remember goal to allow re‑planning
        self.target_path = []    # list of grid coordinates (x,y) to follow, not including current position
        self.current_task = None  # can be "pickup", "delivery", "resort", or None
        self.source_cell = None   # cell from which to pick up an item (for pickup tasks)
        self.dest_cell = None     # cell to drop off an item (for delivery tasks)
        self.target_item_code = None  # desired item code for pickup tasks
        self.carrying_item = None # the Item currently being carried (if any)
        self.speed = 0.0        # current speed in cells per second (will accelerate/decelerate)
        self.show_path = True   # whether to display this bot's planned path in UI (user toggleable)
        self.path_color = color
    
    def set_task_pickup(self, source: Cell, dest: Cell, item_code: str | None = None):
        """Assign a task to pick an item from source cell and deliver it to dest cell."""
        self.current_task = "delivery"
        self.source_cell = source
        self.dest_cell = dest
        self.target_item_code = item_code
        self.carrying_item = None  # not carrying anything yet
        # Compute path to source location
        self._compute_path_to((source.x, source.y))
    
    def set_task_resort(self, cell: Cell):
        """Assign a task to resort the given cell (re-stack items by preference)."""
        self.current_task = "resort"
        self.source_cell = cell  # we'll use source_cell as the target for resort
        self.dest_cell = None
        self.carrying_item = None
        # Compute path to the cell that needs resorting
        self._compute_path_to((cell.x, cell.y))
    
    def _compute_path_to(self, target_coords):
        """Helper to compute an A* path from current position to target (coordinates in grid)."""
        self.goal_coords = target_coords
        start = (round(self.pos[0]), round(self.pos[1]))  # current grid cell (rounded if between cells)
        goal = target_coords
        # Build blocked set using other bots' current (rounded) locations
        blocked = {(round(b.pos[0]), round(b.pos[1])) for b in self.grid.bots if b is not self}
        blocked.discard(target_coords)
        # Also block the immediate next cell of other bots to reduce collisions
        blocked_with_paths = set(blocked)
        blocked_with_paths.update({b.target_path[0] for b in self.grid.bots if b is not self and b.target_path})
        path = find_path(start, goal, blocked_with_paths)
        if path is None:
            # Try again ignoring future steps in case no path found
            path = find_path(start, goal, blocked)

        if path is None:
            self.target_path = []
        else:
            # Remove the start cell only if we're already exactly at its center
            at_center = (abs(self.pos[0] - start[0]) < 1e-6 and
                         abs(self.pos[1] - start[1]) < 1e-6)
            if path and path[0] == start and at_center:
                path = path[1:]
            self.target_path = path
    
    def update(self, dt: float, grid):        # Replan if we lost our path but still have a goal
        if not self.target_path and self.goal_coords is not None:
            self._compute_path_to(self.goal_coords)
            if not self.target_path:
                return

        """
        Update the bot's state for a time step of length dt (in seconds).
        Moves the bot along its path according to its speed, and handles task progression.
        """
        # ---------- BEGIN PATCH: dynamic collision avoid ----------
        if not self.target_path:
            return  # 경로 없음

        next_step = self.target_path[0]
        occupied = {(round(b.pos[0]), round(b.pos[1]))
                    for b in self.grid.bots
                    if b is not self}
        if next_step in occupied:
            # Replan around the blocking bot and try on next update
            self._compute_path_to(self.goal_coords)
            return
        # ----------- END PATCH ------------------------------
        
        
        
        # Determine next cell target from the path
        if not self.target_path:
            return
        next_x, next_y = self.target_path[0]
        dx = next_x - self.pos[0]
        dy = next_y - self.pos[1]
        distance = math.hypot(dx, dy)  # distance to next cell center in grid units (cells)
        
        # Acceleration control: ramp up speed
        if self.speed < config.MAX_SPEED_CELLS_PER_SEC:
            # Increase speed by acceleration amount (max_speed / accel_time per second)
            self.speed += (config.MAX_SPEED_CELLS_PER_SEC / config.ACCEL_TIME) * dt
            if self.speed > config.MAX_SPEED_CELLS_PER_SEC:
                self.speed = config.MAX_SPEED_CELLS_PER_SEC
        
        # Deceleration control: if this is the final step in path, decelerate to stop
        if len(self.target_path) == 1:
            # Only one cell left to move to (goal cell)
            # Reduce speed by deceleration amount
            decel_rate = config.MAX_SPEED_CELLS_PER_SEC / config.DECEL_TIME
            # Ensure we don't go negative
            self.speed -= decel_rate * dt
            if self.speed < 0.5:  # we can treat 0.5 cell/sec as effectively coming to a stop for final placement
                self.speed = 0.5
        
        # Calculate movement distance for this frame
        step = self.speed * dt
        if step >= distance and distance != 0:
            # We can reach (or overshoot) the next cell in this timestep
            self.pos = [next_x, next_y]  # snap to the center of next cell
            # Remove this step from the path
            self.target_path.pop(0)
            # After reaching the cell, check if we completed a phase of the task
            if not self.target_path:
                # Path is now empty, we've arrived at the final target for the current phase
                self._on_reach_destination(grid)
                return
        else:
            # Move closer to the target cell proportionally
            if distance != 0:
                self.pos[0] += (dx / distance) * step
                self.pos[1] += (dy / distance) * step
    
    def _on_reach_destination(self, grid):
        """Handle logic for when the bot reaches a destination (source or dest depending on task)."""
        if self.current_task == "delivery":
            if self.carrying_item is None and self.source_cell is not None:
                # Arrived at source location: pick up item
                cell = grid.get_cell(self.source_cell.x, self.source_cell.y)
                if cell:
                    if self.target_item_code:
                        picked_item = None
                        for i, it in enumerate(cell.items):
                            if it.code == self.target_item_code:
                                picked_item = cell.items.pop(i)
                                break
                    else:
                        picked_item = cell.remove_item()
                    if picked_item:
                        self.carrying_item = picked_item
                # Now plan path to destination to drop off
                if self.dest_cell:
                    self._compute_path_to((self.dest_cell.x, self.dest_cell.y))
                    return
            if self.carrying_item is not None and self.dest_cell is not None:
                # Arrived at destination with an item: drop it off
                grid.get_cell(self.dest_cell.x, self.dest_cell.y).add_item(self.carrying_item)
                # If destination was an outbound cell, the item is considered dispatched (now in outbound stack)
                self.carrying_item = None
                self.target_item_code = None
                # Task complete
                self.current_task = None
                self.source_cell = None
                self.dest_cell = None
                self.goal_coords = None
                # After completing a delivery, the bot will soon be marked idle (and can be sent to rest or get new task)
        elif self.current_task == "resort":
            if self.source_cell is not None:
                # Arrived at the cell that needs re-sorting
                cell = grid.get_cell(self.source_cell.x, self.source_cell.y)
                if cell:
                    temp_cells = []
                    while cell.items:
                        tcell = grid.find_empty_storage_cell(set(temp_cells) | {cell})
                        if tcell is None:
                            break
                        tcell.add_item(cell.remove_item())
                        temp_cells.append(tcell)
                    all_items = []
                    for t in temp_cells:
                        all_items.extend(t.items)
                        t.items = []
                    sorted_items = sorted(all_items, key=lambda it: it.preference, reverse=True)
                    for it in sorted_items:
                        cell.add_item(it)
                # Task complete
                self.current_task = None
                self.source_cell = None
                self.dest_cell = None
                self.goal_coords = None
                # Bot didn't carry anything; it was just reordering at location.
        # When this method finishes, the bot will effectively be idle (no current task, no path).