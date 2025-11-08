"""
Analytics Module
================

This module provides statistical analysis of Minesweeper board configurations.

Overview:
---------
The analytics system generates multiple random Minesweeper boards and analyzes
their properties to create visualizations. This helps understand patterns in
mine placement, number distributions, and board complexity.

Key Features:
1. White Cells Histogram: Shows distribution of empty cells (cells with no mines and no numbers)
2. Number Distribution: Counts how often each number (0-8) appears across all boards
3. Mine Clusters: Analyzes how mines group together (connected mines)
4. Heatmap: Visualizes average mine density in 3×3 neighborhoods

How It Works:
- User specifies board dimensions, mine count, and number of boards to generate
- System generates that many random boards
- For each board, various statistics are computed
- Results are visualized in a 2×2 grid of plots and saved as a PDF

Usage:
- Click the "Analytics" button in the main game window
- Set board dimensions, mine count, and number of boards (e.g., 500 boards)
- Click "Run and Save PDF" and choose where to save the results
- The analysis runs in the background so the game remains responsive
"""

from typing import List, Dict
import numpy as np
import threading

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox,
    QPushButton, QFileDialog, QMessageBox, QWidget
)
from PyQt5.QtCore import Qt

from game_logic import MinesweeperLogic


class AnalyticsRunner:
    """
    Generates multiple Minesweeper boards and computes statistical analytics.
    
    This class is the core of the analytics system. It creates many random
    board configurations and analyzes their properties to generate visualizations.
    
    How it works:
    1. Creates n_boards number of MinesweeperLogic instances
    2. For each board, triggers mine placement (by simulating a first click)
    3. Stores the mine positions and adjacent counts
    4. Computes various statistics across all boards
    5. Generates visualizations (histograms, bar charts, heatmaps)
    
    The analytics help understand:
    - How often empty "white" cells appear
    - Distribution of numbers (0-8) that appear on the board
    - How mines cluster together (connected groups)
    - Spatial patterns in mine placement (heatmap)
    """

    def __init__(self, width: int, height: int, mines: int, n_boards: int):
        self.width = width
        self.height = height
        self.mines = mines
        self.n_boards = max(1, int(n_boards))

        # storage
        self.mines_list: List[np.ndarray] = []
        self.adj_list: List[np.ndarray] = []

    def generate_boards(self):
        """
        Generate all the random boards for analysis.
        
        This method creates n_boards number of Minesweeper boards with random
        mine placements. To get a complete board, we simulate a first click
        at position (0,0), which triggers the mine placement algorithm.
        The safe-first-click feature ensures this position and its neighbors
        are safe, but that's fine for analytics purposes.
        
        The mine positions and adjacent counts are stored for later analysis.
        """
        self.mines_list = []
        self.adj_list = []
        for _ in range(self.n_boards):
            g = MinesweeperLogic(self.width, self.height, self.mines)
            # Trigger mine placement by simulating first click
            # The safe-first-click feature ensures (0,0) is safe, which is fine for analytics
            g.reveal_cell(0, 0)
            # Store copies of the board data
            self.mines_list.append(np.array(g.mines, dtype=bool))
            self.adj_list.append(np.array(g.adjacent_counts, dtype=int))

    def white_cells_per_board(self) -> np.ndarray:
        """
        Count white cells (empty cells with no mines and no numbers) per board.
        
        White cells are cells that have no mine and have an adjacent count of 0
        (meaning no adjacent mines). These are the cells that trigger automatic
        revelation when clicked in the game.
        
        Returns:
            Array with one count per board showing how many white cells each board has
        """
        counts = []
        for mines, adj in zip(self.mines_list, self.adj_list):
            # White cells: no mine AND no adjacent mines (count == 0)
            white = np.logical_and(~mines, adj == 0)
            counts.append(int(np.sum(white)))
        return np.array(counts, dtype=int)

    def number_distribution(self) -> np.ndarray:
        """
        Count how many times each number (0-8) appears across all boards.
        
        This analyzes the distribution of numbers shown on cells. Each cell
        (except mines) shows a number from 0-8 indicating how many adjacent
        mines it has. This method counts how many times each number appears
        across all generated boards.
        
        Returns:
            Array of 9 integers, where index i contains the count of cells
            showing the number i (0 = no number/white cell, 1-8 = number shown)
        """
        bins = np.zeros(9, dtype=int)
        for mines, adj in zip(self.mines_list, self.adj_list):
            # Only count non-mine cells
            valid = ~mines
            vals = adj[valid].flatten()
            # Count occurrences of each number 0-8
            for k in range(9):
                bins[k] += int((vals == k).sum())
        return bins

    def mine_clusters_per_board(self) -> np.ndarray:
        """
        Count the number of mine clusters per board.
        
        A mine cluster is a group of mines that are connected to each other
        (horizontally, vertically, or diagonally). This uses a flood-fill
        algorithm to find all connected components of mines.
        
        For example, if 5 mines are all touching each other, that's 1 cluster.
        If there are 3 separate groups of mines, that's 3 clusters.
        
        Returns:
            Array with one count per board showing how many mine clusters each board has
        """
        H, W = self.height, self.width
        # 8-directional neighbors (including diagonals)
        neigh = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        out = []
        for mines in self.mines_list:
            visited = np.zeros_like(mines, dtype=bool)
            clusters = 0
            # Find all mine clusters using flood-fill
            for r in range(H):
                for c in range(W):
                    if mines[r, c] and not visited[r, c]:
                        # Found a new cluster, explore it
                        clusters += 1
                        stack = [(r, c)]
                        visited[r, c] = True
                        # Flood-fill to mark all connected mines
                        while stack:
                            rr, cc = stack.pop()
                            for dr, dc in neigh:
                                nr, nc = rr + dr, cc + dc
                                if 0 <= nr < H and 0 <= nc < W and mines[nr, nc] and not visited[nr, nc]:
                                    visited[nr, nc] = True
                                    stack.append((nr, nc))
            out.append(clusters)
        return np.array(out, dtype=int)

    def neighbourhood_heatmap(self) -> np.ndarray:
        """
        Compute a heatmap showing average mine density in 3×3 neighborhoods.
        
        For each cell position, this counts how many mines appear in its 3×3
        neighborhood (the cell itself and its 8 neighbors) across all boards,
        then averages it. This creates a heatmap showing where mines tend to
        cluster spatially.
        
        Returns:
            A 2D array (height × width) where each value represents the average
            number of mines in that cell's 3×3 neighborhood across all boards
        """
        H, W = self.height, self.width
        acc = np.zeros((H, W), dtype=float)
        for mines in self.mines_list:
            # Pad the board to handle edge cases
            pad = np.pad(mines.astype(int), pad_width=1, mode='constant', constant_values=0)
            heat = np.zeros((H, W), dtype=int)
            # For each cell, sum mines in its 3×3 neighborhood
            for di in range(3):
                for dj in range(3):
                    heat += pad[di:di+H, dj:dj+W]
            acc += heat
        # Average across all boards
        return acc / max(1, self.n_boards)

    def run_all(self) -> Dict[str, np.ndarray]:
        """
        Run all analytics computations.
        
        This is the main entry point that generates all boards and computes
        all statistics. It returns a dictionary with all the results.
        
        Returns:
            Dictionary containing:
            - "white_counts": array of white cell counts per board
            - "number_distribution": array of number counts (0-8)
            - "cluster_counts": array of cluster counts per board
            - "heatmap": 2D array of average mine density
        """
        self.generate_boards()
        whites = self.white_cells_per_board()
        num_dist = self.number_distribution()
        clusters = self.mine_clusters_per_board()
        heatmap = self.neighbourhood_heatmap()
        return {
            "white_counts": whites,
            "number_distribution": num_dist,
            "cluster_counts": clusters,
            "heatmap": heatmap,
        }

    def plot_and_save_pdf(self, out_path: str):
        # Import matplotlib here so missing dependency produces a handled error
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_pdf import PdfPages
        except Exception as e:
            raise RuntimeError("matplotlib is required for analytics plotting. Install it with `pip install matplotlib`") from e

        data = self.run_all()
        whites = data["white_counts"]
        num_dist = data["number_distribution"]
        clusters = data["cluster_counts"]
        heatmap = data["heatmap"]

        fig, axes = plt.subplots(2, 2, figsize=(10, 8))

        # white cells histogram
        ax = axes[0, 0]
        if len(whites) > 0:
            bins = range(int(whites.min()), int(whites.max()) + 2)
        else:
            bins = [0, 1]
        ax.hist(whites, bins=bins, color='C0', edgecolor='k')
        ax.set_title("Histogram of Number of White Cells per Board")
        ax.set_xlabel("White Cells")
        ax.set_ylabel("# Boards")

        # number distribution 0..8 (extend to 0-9 to match image format)
        ax = axes[0, 1]
        # Extend num_dist to include value 9 (will be 0, but matches image format)
        num_dist_extended = np.append(num_dist, 0)
        ax.bar(range(10), num_dist_extended, color='C1', edgecolor='k')
        ax.set_xticks(range(10))
        ax.set_xlabel("Value Indicated")
        ax.set_ylabel("# Cells")
        ax.set_title("Distribution of Number of Cells with Values")

        # clusters per board
        ax = axes[1, 0]
        if len(clusters) > 0:
            cbins = range(int(clusters.min()), int(clusters.max()) + 2)
        else:
            cbins = [0, 1]
        ax.hist(clusters, bins=cbins, color='C2', edgecolor='k')
        ax.set_title("Number of Mine Clusters per Board")
        ax.set_xlabel("# Mine Clusters")
        ax.set_ylabel("# Boards")

        # heatmap
        ax = axes[1, 1]
        im = ax.imshow(heatmap, cmap='hot', interpolation='nearest')
        ax.set_title("Average Number of Mines on 9x9 radius")
        fig.colorbar(im, ax=ax)

        plt.tight_layout()
        with PdfPages(out_path) as pdf:
            pdf.savefig(fig)
        plt.close(fig)


class AnalyticsDialog(QDialog):
    """
    Dialog for configuring and running analytics.
    
    This dialog allows users to:
    1. Set board dimensions (width, height)
    2. Set number of mines
    3. Set how many boards to generate (e.g., 500 for good statistics)
    4. Run the analysis and save results as a PDF
    
    The analysis runs in a background thread so the GUI remains responsive
    during computation. This is important because generating hundreds or
    thousands of boards can take several seconds.
    """

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setWindowTitle("Minesweeper Analytics")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        row = QHBoxLayout()
        row.addWidget(QLabel("Width:"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(5, 200)
        self.width_spin.setValue(16)
        row.addWidget(self.width_spin)

        row.addWidget(QLabel("Height:"))
        self.height_spin = QSpinBox()
        self.height_spin.setRange(5, 200)
        self.height_spin.setValue(16)
        row.addWidget(self.height_spin)

        row.addWidget(QLabel("Mines:"))
        self.mines_spin = QSpinBox()
        self.mines_spin.setRange(1, 9999)
        self.mines_spin.setValue(40)
        row.addWidget(self.mines_spin)

        layout.addLayout(row)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Number of boards:"))
        self.n_spin = QSpinBox()
        self.n_spin.setRange(1, 20000)
        self.n_spin.setValue(500)
        row2.addWidget(self.n_spin)
        layout.addLayout(row2)

        btn_row = QHBoxLayout()
        self.run_btn = QPushButton("Run and Save PDF")
        self.run_btn.clicked.connect(self.on_run)
        btn_row.addWidget(self.run_btn)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        btn_row.addWidget(self.close_btn)

        layout.addLayout(btn_row)

    def on_run(self):
        width = int(self.width_spin.value())
        height = int(self.height_spin.value())
        mines = int(self.mines_spin.value())
        n = int(self.n_spin.value())

        path, _ = QFileDialog.getSaveFileName(self, "Save analytics PDF", "analytics.pdf", "PDF Files (*.pdf)")
        if not path:
            return

        self.run_btn.setEnabled(False)
        self.run_btn.setText("Running...")

        def background():
            try:
                runner = AnalyticsRunner(width, height, mines, n)
                runner.plot_and_save_pdf(path)
                self._notify_success(path)
            except Exception as e:
                self._notify_error(e)
            finally:
                self._reset_ui()

        t = threading.Thread(target=background, daemon=True)
        t.start()

    def _notify_success(self, path: str):
        def show():
            QMessageBox.information(self, "Analytics", f"Saved analytics PDF to: {path}")
        QApplication = __import__('PyQt5.QtWidgets', fromlist=['QApplication']).QApplication
        QApplication.instance().postEvent(self, _FuncEvent(show))

    def _notify_error(self, exc: Exception):
        def show():
            QMessageBox.critical(self, "Analytics Error", str(exc))
        QApplication = __import__('PyQt5.QtWidgets', fromlist=['QApplication']).QApplication
        QApplication.instance().postEvent(self, _FuncEvent(show))

    def _reset_ui(self):
        def reset():
            self.run_btn.setEnabled(True)
            self.run_btn.setText("Run and Save PDF")
        QApplication = __import__('PyQt5.QtWidgets', fromlist=['QApplication']).QApplication
        QApplication.instance().postEvent(self, _FuncEvent(reset))


# Small helper: use Qt event to execute a function on the main thread.
from PyQt5.QtCore import QEvent, QCoreApplication

class _FuncEvent(QEvent):
    def __init__(self, func):
        super().__init__(QEvent.User)
        self.func = func

    def execute(self):
        self.func()

# Reimplement event() in QDialog to catch _FuncEvent
_orig_event = QDialog.event

def _dialog_event(self, event):
    if isinstance(event, _FuncEvent):
        event.execute()
        return True
    return _orig_event(self, event)

QDialog.event = _dialog_event
