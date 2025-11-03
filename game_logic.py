import numpy as np
from enum import Enum


class CellState(Enum):
    """Represents the state of a cell"""
    HIDDEN = 0
    REVEALED = 1
    FLAGGED = 2


class GameState(Enum):
    """Represents the current state of the game"""
    NOT_STARTED = 0
    PLAYING = 1
    WON = 2
    LOST = 3


class MinesweeperLogic:
    """Core game logic"""
    
    def __init__(self, width, height, mines):
        self.width = width
        self.height = height
        self.total_mines = mines
        
        # Use numpy arrays for efficient board representation
        self.mines = np.zeros((height, width), dtype=bool)  # Mine positions
        self.adjacent_counts = np.zeros((height, width), dtype=np.int8)  # Adjacent mine counts
        self.cell_states = np.full((height, width), CellState.HIDDEN, dtype=object)  # Cell states
        
        self.game_state = GameState.NOT_STARTED
        self.flags_placed = 0
        self.cells_revealed = 0
        self.first_click = True
    
    def _is_valid_position(self, row, col):
        """Check if position is within board boundaries"""
        return 0 <= row < self.height and 0 <= col < self.width
    
    def _get_neighbors(self, row, col):
        """Get all valid neighbor positions for a cell using numpy"""
        # Create offset arrays
        offsets = np.array([[-1, -1], [-1, 0], [-1, 1],
                           [0, -1],           [0, 1],
                           [1, -1],  [1, 0],  [1, 1]])
        
        # Calculate neighbor positions
        neighbors = offsets + np.array([row, col])
        
        # Filter valid positions
        valid_mask = ((neighbors[:, 0] >= 0) & (neighbors[:, 0] < self.height) &
                     (neighbors[:, 1] >= 0) & (neighbors[:, 1] < self.width))
        
        return neighbors[valid_mask]
    
    def _place_mines(self, exclude_row, exclude_col):
        """Place mines randomly using numpy, excluding the first clicked cell and its neighbors"""
        # Create exclusion mask
        exclusion_mask = np.zeros((self.height, self.width), dtype=bool)
        exclusion_mask[exclude_row, exclude_col] = True
        
        # Exclude neighbors
        neighbors = self._get_neighbors(exclude_row, exclude_col)
        for n_row, n_col in neighbors:
            exclusion_mask[n_row, n_col] = True
        
        # Get valid positions for mines
        valid_positions = np.argwhere(~exclusion_mask)
        
        # Randomly select mine positions
        num_mines = min(self.total_mines, len(valid_positions))
        mine_indices = np.random.choice(len(valid_positions), num_mines, replace=False)
        mine_positions = valid_positions[mine_indices]
        
        # Place mines
        for row, col in mine_positions:
            self.mines[row, col] = True
        
        # Calculate adjacent mine counts efficiently
        self._calculate_adjacent_mines()
    
    def _calculate_adjacent_mines(self):
        """Efficient vectorized calculation of adjacent mine counts."""
        padded = np.pad(self.mines.astype(np.int8), 1)
        self.adjacent_counts = (
            padded[:-2, :-2] + padded[:-2, 1:-1] + padded[:-2, 2:] +
            padded[1:-1, :-2] + padded[1:-1, 2:] +
            padded[2:, :-2] + padded[2:, 1:-1] + padded[2:, 2:]
        )

    def reveal_cell(self, row, col):
        """
        Reveal a cell and return list of revealed cells using numpy-optimized flood fill
        Returns: list of (row, col) tuples of all revealed cells
        """
        if not self._is_valid_position(row, col):
            return []
        
        # Handle first click
        if self.first_click:
            self._place_mines(row, col)
            self.first_click = False
            self.game_state = GameState.PLAYING
        
        # Can't reveal flagged or already revealed cells
        if self.cell_states[row, col] in (CellState.FLAGGED, CellState.REVEALED):
            return []
        
        revealed_cells = []
        
        # If mine, game over
        if self.mines[row, col]:
            self.cell_states[row, col] = CellState.REVEALED
            self.game_state = GameState.LOST
            return [(row, col)]
        
        # Flood fill for empty cells using stack-based approach
        to_reveal = [(row, col)]
        visited = np.zeros((self.height, self.width), dtype=bool)
        
        while to_reveal:
            r, c = to_reveal.pop()
            
            if visited[r, c]:
                continue
            
            visited[r, c] = True
            
            if self.cell_states[r, c] == CellState.REVEALED:
                continue
            
            if self.cell_states[r, c] == CellState.FLAGGED:
                continue
            
            self.cell_states[r, c] = CellState.REVEALED
            revealed_cells.append((r, c))
            self.cells_revealed += 1
            
            # If cell has no adjacent mines, reveal neighbors
            if self.adjacent_counts[r, c] == 0:
                neighbors = self._get_neighbors(r, c)
                for n_row, n_col in neighbors:
                    if not visited[n_row, n_col]:
                        to_reveal.append((n_row, n_col))
        
        # Check win condition
        total_cells = self.width * self.height
        if self.cells_revealed == total_cells - self.total_mines:
            self.game_state = GameState.WON
        
        return revealed_cells
    
    def toggle_flag(self, row, col):
        """Toggle flag on a cell. Returns True if flag state changed."""
        if not self._is_valid_position(row, col):
            return False
        
        # Can't flag revealed cells
        if self.cell_states[row, col] == CellState.REVEALED:
            return False
        
        # Toggle flag
        if self.cell_states[row, col] == CellState.FLAGGED:
            self.cell_states[row, col] = CellState.HIDDEN
            self.flags_placed -= 1
        else:
            self.cell_states[row, col] = CellState.FLAGGED
            self.flags_placed += 1
        
        return True
    
    def reveal_all_mines(self):
        """Reveal all mines using numpy (for game over)"""
        mine_positions = np.argwhere(self.mines)
        return [(int(row), int(col)) for row, col in mine_positions]
    
    def get_remaining_mines(self):
        """Get the number of remaining mines (total mines - flags placed)"""
        return self.total_mines - self.flags_placed
    
    def reset(self):
        """Reset the game"""
        self.mines = np.zeros((self.height, self.width), dtype=bool)
        self.adjacent_counts = np.zeros((self.height, self.width), dtype=np.int8)
        self.cell_states = np.full((self.height, self.width), CellState.HIDDEN, dtype=object)
        self.game_state = GameState.NOT_STARTED
        self.flags_placed = 0
        self.cells_revealed = 0
        self.first_click = True