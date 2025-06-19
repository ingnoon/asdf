# pathfinder.py

from heapq import heappush, heappop

def find_path(start, goal, blocked=None, grid_size=(None,None)):
    """
    Find a path from start to goal on a grid using A*.
    - start, goal: (x, y) tuples for starting and target cell coordinates.
    - blocked: a set of (x, y) cells to treat as obstacles (e.g., occupied by bots or impassable).
    - grid_size: (width, height) of the grid (if not provided, will infer from global config or environment).
    Returns: a list of (x, y) coordinates from start to goal (inclusive) representing the path, or None if no path.
    """
    if blocked is None:
        blocked = set()
    width, height = grid_size
    # If grid size not provided, use default config (to ensure in-bounds checks)
    if width is None or height is None:
        import config
        width, height = config.GRID_WIDTH, config.GRID_HEIGHT
    
    # A* algorithm implementation
    start_node = start
    goal_node = goal
    if start_node == goal_node:
        return [start_node]  # trivial case: starting at goal
    
    # Heuristic function: Manhattan distance
    def heuristic(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    # Open set (priority queue of (f_score, count, node))
    open_set = []
    heappush(open_set, (0 + heuristic(start_node, goal_node), 0, start_node))
    
    came_from = {}  # for path reconstruction
    # Cost from start to this node (g-score)
    g_score = {start_node: 0}
    # f_score = g_score + heuristic
    f_score = {start_node: heuristic(start_node, goal_node)}
    
    # A set for quick membership testing of nodes in open_set
    open_set_nodes = {start_node}
    
    # Counter for tie-breaking in the priority queue
    counter = 0
    
    while open_set:
        # Pop the node with lowest f_score
        _, _, current = heappop(open_set)
        open_set_nodes.discard(current)
        
        # If reached goal, reconstruct path
        if current == goal_node:
            # Reconstruct path by walking backwards from goal to start
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path
        
        # Explore neighbors (4-directional)
        x, y = current
        for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
            nx, ny = x + dx, y + dy
            # Bounds check
            if nx < 0 or nx >= width or ny < 0 or ny >= height:
                continue
            neighbor = (nx, ny)
            # Skip if neighbor is blocked
            if neighbor in blocked:
                continue
            # We could also skip neighbor if it's a wall or impassable cell by design (not applicable in open floor warehouse aside from blocked spots).
            
            tentative_g = g_score[current] + 1  # cost to move to neighbor (assume each move cost = 1)
            if tentative_g < g_score.get(neighbor, float('inf')):
                # Found a better path to neighbor
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score[neighbor] = tentative_g + heuristic(neighbor, goal_node)
                if neighbor not in open_set_nodes:
                    counter += 1
                    heappush(open_set, (f_score[neighbor], counter, neighbor))
                    open_set_nodes.add(neighbor)
    # If open_set is empty and goal not reached, no path
    return None