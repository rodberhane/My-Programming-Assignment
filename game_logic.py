"""
Game Logic Module
=================

This module contains the core Minesweeper game logic, completely independent
of the user interface. This separation allows the same game logic to work
with different UIs (GUI, text-based, etc.).

Overview:
---------
The MinesweeperLogic class manages:
- Board state (mine positions, cell states, adjacent counts)
- Game flow (revealing cells, flagging, win/loss detection)
- Safe-first-click feature (first click is always safe)

Key Concepts:
- Cell States: HIDDEN (unrevealed), REVEALED (shown), FLAGGED (marked as mine)
- Adjacent Counts: Each cell stores how many mines are in its 8 neighbors
- Flood Fill: When revealing an empty cell (count=0), automatically reveal neighbors
- Win Condition: All non-mine cells are revealed

How It Works:
1. Board is created with specified dimensions and mine count
2. Mines are NOT placed until the first cell is clicked (safe-first-click)
3. When first cell is clicked, mines are randomly placed (excluding clicked cell and neighbors)
4. Adjacent mine counts are calculated for all cells
5. Revealing a cell triggers flood-fill if it's empty
6. Game ends when a mine is clicked (LOST) or all safe cells are revealed (WON)
"""

import numpy as np
from enum import Enum


class CellState(Enum):
    """
    Represents the state of a single cell on the board.
    
    - HIDDEN: Cell is not yet revealed (default state)
    - REVEALED: Cell has been clicked and shows its content (number or empty)
    - FLAGGED: Player has marked this cell as containing a mine (right-click)
    """
    HIDDEN = 0
    REVEALED = 1
    FLAGGED = 2


class GameState(Enum):
    """
    Represents the overall state of the game.
    
    - NOT_STARTED: Game created but no moves made yet
    - PLAYING: Game is in progress
    - WON: Player successfully revealed all non-mine cells
    - LOST: Player clicked on a mine
    """
    NOT_STARTED = 0
    PLAYING = 1
    WON = 2
    LOST = 3


class MinesweeperLogic:
    """
    Core Minesweeper game logic.
    
    This class manages the entire game state and rules. It uses numpy arrays
    for efficient board representation and calculations.
    
    Key Features:
    - Safe-first-click: First click is always safe (no mine there or nearby)
    - Flood-fill revelation: Empty cells automatically reveal their neighbors
    - Efficient mine counting: Uses vectorized numpy operations
    - Win/loss detection: Automatically tracks game completion
    
    Attributes:
        width: Board width (number of columns)
        height: Board height (number of rows)
        total_mines: Total number of mines on the board
        mines: 2D boolean array - True where mines are placed
        adjacent_counts: 2D integer array - count of adjacent mines (0-8)
        cell_states: 2D array of CellState - current state of each cell
        game_state: Current GameState (NOT_STARTED, PLAYING, WON, LOST)
        flags_placed: Number of flags currently on the board
        cells_revealed: Number of cells that have been revealed
        first_click: Whether the first click has happened yet
    """
    
    def __init__(self, width, height, mines):
        """
        Initialize a new Minesweeper game.
        
        Args:
            width: Number of columns (board width)
            height: Number of rows (board height)
            mines: Number of mines to place on the board
        """
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
        """
        Check if a position is within the board boundaries.
        
        Args:
            row: Row index
            col: Column index
            
        Returns:
            True if the position is valid, False otherwise
        """
        return 0 <= row < self.height and 0 <= col < self.width
    
    def _get_neighbors(self, row, col):
        """
        Get all valid neighbor positions for a cell (8-directional).
        
        This returns all 8 neighbors (including diagonals) that are within
        the board boundaries. Uses numpy for efficient computation.
        
        Args:
            row: Row index of the cell
            col: Column index of the cell
            
        Returns:
            Array of (row, col) tuples for all valid neighbors
        """
        # Create offset arrays for 8 neighbors
        offsets = np.array([[-1, -1], [-1, 0], [-1, 1],
                           [0, -1],           [0, 1],
                           [1, -1],  [1, 0],  [1, 1]])
        
        # Calculate neighbor positions
        neighbors = offsets + np.array([row, col])
        
        # Filter valid positions (within board boundaries)
        valid_mask = ((neighbors[:, 0] >= 0) & (neighbors[:, 0] < self.height) &
                     (neighbors[:, 1] >= 0) & (neighbors[:, 1] < self.width))
        
        return neighbors[valid_mask]
    
    def _place_mines(self, exclude_row, exclude_col):
        """
        Place mines randomly on the board, excluding the first clicked cell and its neighbors.
        
        This implements the "safe-first-click" feature. The first cell clicked and all
        its 8 neighbors are guaranteed to be safe (no mines). This makes the game
        more fair and less frustrating.
        
        Args:
            exclude_row: Row of the first clicked cell (to exclude)
            exclude_col: Column of the first clicked cell (to exclude)
        """
        # Create exclusion mask - mark cells that cannot have mines
        exclusion_mask = np.zeros((self.height, self.width), dtype=bool)
        exclusion_mask[exclude_row, exclude_col] = True
        
        # Exclude all neighbors of the first click
        neighbors = self._get_neighbors(exclude_row, exclude_col)
        for n_row, n_col in neighbors:
            exclusion_mask[n_row, n_col] = True
        
        # Get valid positions for mines (all cells except excluded ones)
        valid_positions = np.argwhere(~exclusion_mask)
        
        # Randomly select mine positions
        num_mines = min(self.total_mines, len(valid_positions))
        mine_indices = np.random.choice(len(valid_positions), num_mines, replace=False)
        mine_positions = valid_positions[mine_indices]
        
        # Place mines
        for row, col in mine_positions:
            self.mines[row, col] = True
        
        # Calculate adjacent mine counts for all cells
        self._calculate_adjacent_mines()
    
    def _calculate_adjacent_mines(self):
        """
        Efficiently calculate how many mines are adjacent to each cell.
        
        This uses a vectorized numpy approach: it pads the mine array and
        sums up the 8 neighbors for each cell. This is much faster than
        looping through each cell individually.
        
        The result is stored in self.adjacent_counts, where each cell contains
        a number from 0-8 indicating how many of its 8 neighbors contain mines.
        """
        # Pad the board with zeros to handle edge cases
        padded = np.pad(self.mines.astype(np.int8), 1)
        # Sum all 8 neighbors for each cell using array slicing
        self.adjacent_counts = (
            padded[:-2, :-2] + padded[:-2, 1:-1] + padded[:-2, 2:] +
            padded[1:-1, :-2] + padded[1:-1, 2:] +
            padded[2:, :-2] + padded[2:, 1:-1] + padded[2:, 2:]
        )

    def reveal_cell(self, row, col):
        """
        Reveal a cell and handle flood-fill for empty cells.
        
        This is the main method for revealing cells. It handles:
        1. First click: Places mines (excluding clicked cell and neighbors)
        2. Mine click: Game over (LOST)
        3. Empty cell: Flood-fill to reveal connected empty cells
        4. Number cell: Just reveal that cell
        5. Win detection: Check if all safe cells are revealed
        
        The flood-fill algorithm automatically reveals all connected empty cells
        (cells with adjacent_count = 0) when one is clicked. This is the classic
        Minesweeper behavior where clicking an empty area reveals a large region.
        
        Args:
            row: Row index of cell to reveal
            col: Column index of cell to reveal
            
        Returns:
            List of (row, col) tuples for all cells that were revealed
            (including the clicked cell and any flood-filled cells)
        """
        if not self._is_valid_position(row, col):
            return []
        
        # Handle first click - place mines now (safe-first-click feature)
        if self.first_click:
            self._place_mines(row, col)
            self.first_click = False
            self.game_state = GameState.PLAYING
        
        # Can't reveal flagged or already revealed cells
        if self.cell_states[row, col] in (CellState.FLAGGED, CellState.REVEALED):
            return []
        
        revealed_cells = []
        
        # If mine, game over immediately
        if self.mines[row, col]:
            self.cell_states[row, col] = CellState.REVEALED
            self.game_state = GameState.LOST
            return [(row, col)]
        
        # Flood fill for empty cells using stack-based approach
        # This reveals all connected empty cells (adjacent_count = 0)
        to_reveal = [(row, col)]
        visited = np.zeros((self.height, self.width), dtype=bool)
        
        while to_reveal:
            r, c = to_reveal.pop()
            
            if visited[r, c]:
                continue
            
            visited[r, c] = True
            
            # Skip if already revealed or flagged
            if self.cell_states[r, c] == CellState.REVEALED:
                continue
            
            if self.cell_states[r, c] == CellState.FLAGGED:
                continue
            
            # Reveal this cell
            self.cell_states[r, c] = CellState.REVEALED
            revealed_cells.append((r, c))
            self.cells_revealed += 1
            
            # If cell has no adjacent mines, reveal all neighbors (flood-fill)
            if self.adjacent_counts[r, c] == 0:
                neighbors = self._get_neighbors(r, c)
                for n_row, n_col in neighbors:
                    if not visited[n_row, n_col]:
                        to_reveal.append((n_row, n_col))
        
        # Check win condition: all non-mine cells are revealed
        total_cells = self.width * self.height
        if self.cells_revealed == total_cells - self.total_mines:
            self.game_state = GameState.WON
        
        return revealed_cells
    
    def toggle_flag(self, row, col):
        """
        Toggle a flag on a cell (right-click action).
        
        Flags are used to mark cells that the player thinks contain mines.
        This helps players keep track of suspected mines without revealing them.
        
        Args:
            row: Row index of cell
            col: Column index of cell
            
        Returns:
            True if the flag state was changed, False otherwise
            (returns False if cell is invalid or already revealed)
        """
        if not self._is_valid_position(row, col):
            return False
        
        # Can't flag revealed cells
        if self.cell_states[row, col] == CellState.REVEALED:
            return False
        
        # Toggle flag state
        if self.cell_states[row, col] == CellState.FLAGGED:
            self.cell_states[row, col] = CellState.HIDDEN
            self.flags_placed -= 1
        else:
            self.cell_states[row, col] = CellState.FLAGGED
            self.flags_placed += 1
        
        return True
    
    def reveal_all_mines(self):
        """
        Get positions of all mines (for game over display).
        
        This is used when the game ends to show where all the mines were.
        
        Returns:
            List of (row, col) tuples for all mine positions
        """
        mine_positions = np.argwhere(self.mines)
        return [(int(row), int(col)) for row, col in mine_positions]
    
    def get_remaining_mines(self):
        """
        Calculate remaining mines (for display counter).
        
        This is the number shown in the mine counter display. It's calculated
        as total mines minus flags placed. It can go negative if the player
        places more flags than there are mines.
        
        Returns:
            Number of remaining mines (total_mines - flags_placed)
        """
        return self.total_mines - self.flags_placed
    
    def reset(self):
        """
        Reset the game to initial state.
        
        This clears the board, removes all mines, resets all cell states,
        and prepares for a new game. The board dimensions and mine count
        remain the same.
        """
        self.mines = np.zeros((self.height, self.width), dtype=bool)
        self.adjacent_counts = np.zeros((self.height, self.width), dtype=np.int8)
        self.cell_states = np.full((self.height, self.width), CellState.HIDDEN, dtype=object)
        self.game_state = GameState.NOT_STARTED
        self.flags_placed = 0
        self.cells_revealed = 0
        self.first_click = True