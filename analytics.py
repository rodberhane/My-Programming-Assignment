"""
Analytics module for Minesweeper board analysis
Provides functions for analyzing generated boards
"""
import numpy as np
from typing import List, Dict, Tuple
from game_logic import MinesweeperLogic


def generate_boards(n: int, width: int, height: int, mines: int) -> List[Dict]:
    """
    Generate n boards with the given configuration.
    Uses first safe click logic - randomly selects first click position.
    
    Returns:
        List of board dictionaries, each containing:
        - 'mines': numpy array of mine positions
        - 'adjacent_counts': numpy array of adjacent mine counts
        - 'width': board width
        - 'height': board height
        - 'mines_count': number of mines configured
    """
    boards = []
    logic = MinesweeperLogic(width, height, mines)
    
    for _ in range(n):
        # Random first click position for each board
        first_row = np.random.randint(0, height)
        first_col = np.random.randint(0, width)
        board = logic.generate_board(first_row, first_col)
        board['mines_count'] = mines  # Store original mine count
        boards.append(board)
        logic.reset()
    
    return boards


def count_white_cells(board: Dict) -> int:
    """
    Count white cells (cells with no mine and no number, i.e., adjacent_count == 0).
    
    Args:
        board: Board dictionary with 'mines' and 'adjacent_counts'
    
    Returns:
        Number of white cells
    """
    mines = board['mines']
    adjacent_counts = board['adjacent_counts']
    
    # White cells are those with no mine and adjacent_count == 0
    white_cells = (~mines) & (adjacent_counts == 0)
    return int(np.sum(white_cells))


def analyze_white_cells(boards: List[Dict]) -> np.ndarray:
    """
    Analyze white cells across all boards.
    
    Returns:
        Array of white cell counts for each board
    """
    return np.array([count_white_cells(board) for board in boards])


def analyze_cell_numbers(boards: List[Dict]) -> Dict[int, int]:
    """
    Analyze the distribution of numbers shown in each cell.
    Only counts non-mine cells (mine cells don't display numbers).
    
    Returns:
        Dictionary mapping number (0-8) to count of occurrences
    """
    distribution = {i: 0 for i in range(9)}  # 0-8
    
    for board in boards:
        adjacent_counts = board['adjacent_counts']
        mines = board['mines']
        
        # Only count non-mine cells (mine cells don't show numbers)
        for row in range(board['height']):
            for col in range(board['width']):
                if not mines[row, col]:  # Only non-mine cells
                    count = int(adjacent_counts[row, col])
                    distribution[count] += 1
    
    return distribution


def analyze_white_vs_numbered(boards: List[Dict]) -> Dict[str, int]:
    """
    Analyze white cells vs numbered cells.
    White cells: non-mine cells with 0 adjacent mines
    Numbered cells: non-mine cells with 1-8 adjacent mines
    
    Returns:
        Dictionary with 'white' and 'numbered' counts
    """
    white_count = 0
    numbered_count = 0
    
    for board in boards:
        adjacent_counts = board['adjacent_counts']
        mines = board['mines']
        
        for row in range(board['height']):
            for col in range(board['width']):
                if not mines[row, col]:  # Only non-mine cells
                    if adjacent_counts[row, col] == 0:
                        white_count += 1
                    else:
                        numbered_count += 1
    
    return {'white': white_count, 'numbered': numbered_count}


def find_mine_clusters(board: Dict) -> Tuple[int, Dict, np.ndarray]:
    """
    Find mine clusters on a board and return detailed cluster information.
    A mine cluster is a group of mines that touch each other 
    horizontally, vertically, or diagonally.
    
    Returns:
        Tuple of (num_clusters, cluster_info_dict, cluster_map)
        - num_clusters: total number of clusters
        - cluster_info_dict: dict mapping cluster_id to list of (row, col) positions
        - cluster_map: 2D array where each mine cell has its cluster ID, -1 for non-mines
    """
    mines = board['mines']
    height, width = mines.shape
    
    # Create visited array and cluster map
    visited = np.zeros_like(mines, dtype=bool)
    cluster_map = np.full((height, width), -1, dtype=int)
    cluster_info = {}
    cluster_id = 0
    
    def dfs(row, col, cid):
        """Depth-first search to mark all connected mines"""
        if (row < 0 or row >= height or col < 0 or col >= width or 
            visited[row, col] or not mines[row, col]):
            return
        
        visited[row, col] = True
        cluster_map[row, col] = cid
        
        if cid not in cluster_info:
            cluster_info[cid] = []
        cluster_info[cid].append((row, col))
        
        # Check all 8 neighbors
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                dfs(row + dr, col + dc, cid)
    
    # Find all clusters
    for row in range(height):
        for col in range(width):
            if mines[row, col] and not visited[row, col]:
                dfs(row, col, cluster_id)
                cluster_id += 1
    
    return cluster_id, cluster_info, cluster_map


def find_mine_clusters_count(board: Dict) -> int:
    """Find just the number of mine clusters (for histogram)"""
    num_clusters, _, _ = find_mine_clusters(board)
    return num_clusters


def analyze_mine_clusters(boards: List[Dict]) -> np.ndarray:
    """
    Analyze mine clusters across all boards.
    
    Returns:
        Array of cluster counts for each board
    """
    return np.array([find_mine_clusters_count(board) for board in boards])


def get_sample_board_clusters(boards: List[Dict]) -> Dict:
    """
    Get cluster information for a sample board (first board).
    Used for visualization.
    
    Returns:
        Dictionary with cluster information for visualization
    """
    if not boards:
        return None
    
    sample_board = boards[0]
    num_clusters, cluster_info, cluster_map = find_mine_clusters(sample_board)
    
    # Calculate cluster sizes and identify isolated mines (clusters of size 1)
    cluster_sizes = {cid: len(positions) for cid, positions in cluster_info.items()}
    isolated_mines = sum(1 for size in cluster_sizes.values() if size == 1)
    cluster_mines = sum(size for size in cluster_sizes.values() if size > 1)
    
    # Get largest clusters
    sorted_clusters = sorted(cluster_sizes.items(), key=lambda x: x[1], reverse=True)
    
    return {
        'num_clusters': num_clusters,
        'isolated_mines': isolated_mines,
        'cluster_mines': cluster_mines,
        'largest_cluster_size': sorted_clusters[0][1] if sorted_clusters else 0,
        'cluster_info': cluster_info,
        'cluster_map': cluster_map,
        'cluster_sizes': cluster_sizes,
        'board': sample_board
    }


def calculate_mine_neighborhood_heatmap(boards: List[Dict]) -> np.ndarray:
    """
    Calculate the average adjacent mine count for each cell position across all boards.
    This shows how many mines are in the 8 surrounding cells (not including the cell itself).
    
    Returns:
        2D numpy array representing the heatmap
    """
    if not boards:
        return np.array([])
    
    height = boards[0]['height']
    width = boards[0]['width']
    heatmap = np.zeros((height, width), dtype=float)
    
    for board in boards:
        # Use adjacent_counts which already has the correct calculation
        # (number of mines in 8 surrounding cells, excluding the cell itself)
        adjacent_counts = board['adjacent_counts']
        heatmap += adjacent_counts.astype(float)
    
    # Average across all boards
    heatmap = heatmap / len(boards)
    
    return heatmap


def run_all_analytics(boards: List[Dict]) -> Dict:
    """
    Run all analytics on the given boards.
    
    Returns:
        Dictionary containing all analytics results:
        - 'white_cells': array of white cell counts per board
        - 'cell_numbers': distribution of numbers (0-8) for non-mine cells
        - 'white_vs_numbered': dict with 'white' and 'numbered' counts
        - 'mine_clusters': array of cluster counts per board
        - 'sample_clusters': cluster information for visualization
        - 'heatmap': 2D array of average mine neighborhood
    """
    return {
        'white_cells': analyze_white_cells(boards),
        'cell_numbers': analyze_cell_numbers(boards),
        'white_vs_numbered': analyze_white_vs_numbered(boards),
        'mine_clusters': analyze_mine_clusters(boards),
        'sample_clusters': get_sample_board_clusters(boards),
        'heatmap': calculate_mine_neighborhood_heatmap(boards),
        'num_boards': len(boards),
        'board_config': {
            'width': boards[0]['width'] if boards else 0,
            'height': boards[0]['height'] if boards else 0,
            'mines': boards[0].get('mines_count', sum(np.sum(board['mines']) for board in boards) // len(boards)) if boards else 0
        }
    }


# PyQt5 Analytics Dialog
try:
    from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                                 QLabel, QProgressBar, QMessageBox, QScrollArea, QWidget)
    from PyQt5.QtCore import Qt, QThread, pyqtSignal
    from PyQt5.QtGui import QFont
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.backends.backend_pdf import PdfPages
    from matplotlib.figure import Figure
    import matplotlib.pyplot as plt
    import os
    from datetime import datetime
    
    class AnalyticsWorker(QThread):
        """Worker thread for generating boards and analytics"""
        finished = pyqtSignal(object)
        progress = pyqtSignal(int)
        
        def __init__(self, n_boards, width, height, mines):
            super().__init__()
            self.n_boards = n_boards
            self.width = width
            self.height = height
            self.mines = mines
        
        def run(self):
            boards = []
            logic = MinesweeperLogic(self.width, self.height, self.mines)
            
            for i in range(self.n_boards):
                first_row = np.random.randint(0, self.height)
                first_col = np.random.randint(0, self.width)
                board = logic.generate_board(first_row, first_col)
                board['mines_count'] = self.mines
                boards.append(board)
                logic.reset()
                self.progress.emit(int((i + 1) / self.n_boards * 100))
            
            results = run_all_analytics(boards)
            self.finished.emit(results)
    
    
    class ChartDialog(QDialog):
        """Individual dialog window for a single chart"""
        
        def __init__(self, parent, title, figure, chart_key, on_close_callback):
            super().__init__(parent)
            self.setWindowTitle(title)
            self.figure = figure
            self.chart_key = chart_key
            self.on_close_callback = on_close_callback
            self.setMinimumSize(800, 600)
            
            layout = QVBoxLayout(self)
            canvas = FigureCanvas(figure)
            layout.addWidget(canvas)
        
        def closeEvent(self, event):
            """Notify parent when this dialog closes"""
            if self.on_close_callback:
                self.on_close_callback(self.chart_key)
            event.accept()
    
    
    class AnalyticsDialog(QDialog):
        """PyQt5 dialog for displaying Minesweeper analytics"""
        
        def __init__(self, parent=None, width=30, height=16, mines=99):
            super().__init__(parent)
            self.width = width
            self.height = height
            self.mines = mines
            self.analytics_results = None
            self.figures = {}
            self.chart_dialogs = {}  # Track open chart dialogs
            self.closed_charts = set()  # Track which charts have been closed
            self.setWindowTitle("Minesweeper Analytics - Generating...")
            self.setMinimumSize(400, 200)
            self.init_ui()
            self.generate_analytics()
        
        def init_ui(self):
            """Initialize the user interface"""
            layout = QVBoxLayout(self)
            
            # Title
            title = QLabel("Generating Analytics...")
            title.setFont(QFont('Arial', 16, QFont.Bold))
            title.setAlignment(Qt.AlignCenter)
            layout.addWidget(title)
            self.title_label = title
            
            # Progress bar
            self.progress = QProgressBar()
            self.progress.setRange(0, 100)
            layout.addWidget(self.progress)
            
            # Info label
            info = QLabel("Charts will open in separate windows when ready.")
            info.setAlignment(Qt.AlignCenter)
            layout.addWidget(info)
        
        def generate_analytics(self):
            """Generate boards and analytics in background thread"""
            self.title_label.setText(f"Generating Analytics for {self.width}x{self.height} Board with {self.mines} Mines...")
            self.progress.setValue(0)
            
            # Use 100 boards by default for good statistics
            n_boards = 100
            
            self.worker = AnalyticsWorker(n_boards, self.width, self.height, self.mines)
            self.worker.progress.connect(self.progress.setValue)
            self.worker.finished.connect(self.on_analytics_complete)
            self.worker.start()
        
        def on_analytics_complete(self, results):
            """Handle completion of analytics generation"""
            self.analytics_results = results
            self.title_label.setText("Opening Chart Windows...")
            self.progress.setValue(100)
            self.display_results()
        
        def display_results(self):
            """Display all analytics charts in separate windows"""
            if not self.analytics_results:
                return
            
            results = self.analytics_results
            
            # 1. Mine Neighborhood Heatmap
            self.create_heatmap(results)
            
            # 2. Bar Chart
            self.create_bar_chart(results)
            
            # 3. Pie Chart
            self.create_pie_chart(results)
            
            # 4. Mine Clusters Analysis
            self.create_clusters_chart(results)
            
            # Open all chart windows
            self.open_chart_windows()
        
        def on_chart_closed(self, chart_key):
            """Called when a chart dialog is closed"""
            self.closed_charts.add(chart_key)
            
            # Check if all charts are closed
            if len(self.closed_charts) == len(self.figures):
                # All charts closed, save to PDF and close main dialog
                self.save_to_pdf()
                self.close()
        
        def open_chart_windows(self):
            """Open separate windows for each chart"""
            chart_titles = {
                'heatmap': 'Mine Neighborhood Heatmap',
                'bar_chart': 'Cell Distribution by Adjacent Mine Count',
                'pie_chart': 'White vs Numbered Cells',
                'mine_clusters': 'Mine Clusters Analysis'
            }
            
            for key, fig in self.figures.items():
                title = chart_titles.get(key, key.replace('_', ' ').title())
                dialog = ChartDialog(self, title, fig, key, self.on_chart_closed)
                dialog.show()  # Show non-modal
                self.chart_dialogs[key] = dialog
        
        def create_heatmap(self, results):
            """Create mine neighborhood heatmap with mine markers"""
            heatmap = results['heatmap']
            if heatmap.size == 0:
                return
            
            sample_clusters = results.get('sample_clusters')
            config = results['board_config']
            
            fig = Figure(figsize=(12, 7))
            ax = fig.add_subplot(111)
            
            # Create heatmap with custom colormap matching the image
            # 0-3: dark blue shades, 4-5: purple-red, 6-8: red shades
            from matplotlib.colors import LinearSegmentedColormap
            colors = ['#000033', '#000066', '#000099', '#0000CC',  # 0-3: dark blue
                     '#6600CC', '#CC00CC',  # 4-5: purple-red
                     '#FF0066', '#FF3333', '#FF6666']  # 6-8: red
            n_bins = 9
            cmap = LinearSegmentedColormap.from_list('mine_heatmap', colors, N=n_bins)
            
            im = ax.imshow(heatmap, cmap=cmap, interpolation='nearest', 
                          aspect='auto', origin='upper', vmin=0, vmax=8)
            
            # Add mine markers from sample board
            if sample_clusters and sample_clusters.get('board'):
                mines = sample_clusters['board']['mines']
                mine_positions = np.argwhere(mines)
                for row, col in mine_positions:
                    ax.text(col, row, '☆', ha='center', va='center',
                           fontsize=10, color='white', weight='bold')
            
            ax.set_title(f"Mine Neighborhood Heatmap\n{config['width']}x{config['height']} Board, {config['mines']} Mines",
                        fontsize=14, fontweight='bold', pad=15)
            ax.set_xlabel("Column", fontsize=11)
            ax.set_ylabel("Row", fontsize=11)
            
            # Add colorbar
            cbar = fig.colorbar(im, ax=ax, label="Adjacent Mines", shrink=0.8)
            cbar.set_ticks(range(9))
            cbar.ax.tick_params(labelsize=9)
            
            # Add legend for mines
            if sample_clusters and sample_clusters.get('board'):
                from matplotlib.patches import Patch
                legend_elements = [plt.Line2D([0], [0], marker='*', color='w',
                                             markerfacecolor='white', markersize=10,
                                             markeredgecolor='black', markeredgewidth=0.5,
                                             label='☆ Mines', linestyle='None')]
                ax.legend(handles=legend_elements, loc='upper right', 
                         bbox_to_anchor=(1.15, 0.95), fontsize=9)
            
            fig.tight_layout()
            self.figures["heatmap"] = fig
        
        def create_bar_chart(self, results):
            """Create bar chart for cell distribution by adjacent mine count"""
            cell_numbers = results['cell_numbers']
            numbers = list(cell_numbers.keys())
            counts = list(cell_numbers.values())
            
            # Color scheme matching the example
            colors = ['#5B9BD5', '#70AD47', '#FF6B6B', '#9370DB', '#FFA500',
                     '#20B2AA', '#FFD700', '#C0C0C0', '#808080']
            
            fig = Figure(figsize=(10, 6))
            ax = fig.add_subplot(111)
            
            bars = ax.bar(numbers, counts, color=colors[:len(numbers)], 
                         edgecolor='black', linewidth=1.5)
            ax.set_xlabel("Number of Adjacent Mines", fontsize=12)
            ax.set_ylabel("Cell Count", fontsize=12)
            ax.set_title("Cell Distribution by Adjacent Mine Count", 
                        fontsize=14, fontweight='bold')
            ax.set_xticks(numbers)
            ax.grid(axis='y', alpha=0.3, linestyle='--')
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{int(height)}', ha='center', va='bottom', fontsize=9)
            
            fig.tight_layout()
            self.figures["bar_chart"] = fig
        
        def create_pie_chart(self, results):
            """Create pie chart for white vs numbered cells"""
            white_vs_numbered = results['white_vs_numbered']
            white_count = white_vs_numbered['white']
            numbered_count = white_vs_numbered['numbered']
            total = white_count + numbered_count
            
            fig = Figure(figsize=(8, 6))
            ax = fig.add_subplot(111)
            
            sizes = [white_count, numbered_count]
            labels = ['White Cells', 'Numbered Cells']
            colors_pie = ['#5B9BD5', '#FF6B6B']
            explode = (0.05, 0.05)
            
            wedges, texts, autotexts = ax.pie(sizes, explode=explode, labels=labels,
                                             colors=colors_pie,
                                             autopct=lambda pct: f'{pct:.1f}%\n({int(pct/100*total)} cells)',
                                             shadow=True, startangle=90,
                                             textprops={'fontsize': 11})
            
            ax.set_title("White vs Numbered Cells", fontsize=14, fontweight='bold', pad=20)
            fig.tight_layout()
            self.figures["pie_chart"] = fig
        
        def create_clusters_chart(self, results):
            """Create mine clusters analysis visualization"""
            sample_clusters = results.get('sample_clusters')
            if not sample_clusters:
                return
            
            cluster_map = sample_clusters['cluster_map']
            cluster_sizes = sample_clusters['cluster_sizes']
            num_clusters = sample_clusters['num_clusters']
            isolated_mines = sample_clusters['isolated_mines']
            largest_size = sample_clusters['largest_cluster_size']
            
            height, width = cluster_map.shape
            
            # Separate clusters from isolated mines
            clusters_only = [(cid, size) for cid, size in cluster_sizes.items() if size > 1]
            isolated = [(cid, size) for cid, size in cluster_sizes.items() if size == 1]
            
            # Get top 5 largest clusters
            sorted_clusters = sorted(clusters_only, key=lambda x: x[1], reverse=True)
            top_5_clusters = sorted_clusters[:5]
            
            # Color palette
            cluster_colors = {-1: [0.2, 0.2, 0.2]}  # Dark grey for non-mines
            
            # Top 5 colors
            top_colors = ['#1f77b4', '#aec7e8', '#ff7f0e', '#9467bd', '#2ca02c']
            for idx, (cid, size) in enumerate(top_5_clusters):
                color = top_colors[idx].lstrip('#')
                rgb = tuple(int(color[i:i+2], 16)/255.0 for i in (0, 2, 4))
                cluster_colors[cid] = rgb
            
            # Other cluster colors
            other_colors = ['#d62728', '#ff9896', '#c5b0d5', '#c49c94', '#f7b6d3', 
                           '#dbdb8d', '#9edae5', '#8c564b', '#e377c2', '#bcbd22']
            other_idx = 0
            for cid, size in sorted_clusters[5:]:
                color = other_colors[other_idx % len(other_colors)].lstrip('#')
                rgb = tuple(int(color[i:i+2], 16)/255.0 for i in (0, 2, 4))
                cluster_colors[cid] = rgb
                other_idx += 1
            
            # Isolated mines are white
            for cid, size in isolated:
                cluster_colors[cid] = [1.0, 1.0, 1.0]
            
            # Create visualization
            fig = Figure(figsize=(12, 8))
            ax = fig.add_subplot(111)
            
            # Create color array
            vis_array = np.zeros((height, width, 3))
            for row in range(height):
                for col in range(width):
                    cid = cluster_map[row, col]
                    if cid == -1:
                        vis_array[row, col] = cluster_colors[-1]
                    elif cid in cluster_colors:
                        vis_array[row, col] = cluster_colors[cid]
                    else:
                        vis_array[row, col] = [1.0, 1.0, 1.0]
            
            ax.imshow(vis_array, aspect='auto', origin='upper')
            ax.set_title(f"Mine Clusters Analysis\n{num_clusters} clusters, {isolated_mines} isolated mines, "
                        f"Largest cluster: {largest_size} mines",
                        fontsize=14, fontweight='bold', pad=15)
            ax.set_xlabel("Column", fontsize=11)
            ax.set_ylabel("Row", fontsize=11)
            
            # Add legend
            legend_elements = []
            for idx, (cid, size) in enumerate(top_5_clusters):
                color = top_colors[idx]
                legend_elements.append(plt.Rectangle((0,0),1,1, facecolor=color,
                                                     edgecolor='black', label=f'Cluster {idx+1} ({size} mines)'))
            legend_elements.append(plt.Rectangle((0,0),1,1, facecolor='white',
                                               edgecolor='black', label='Isolated mines'))
            
            ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.15, 1), fontsize=9)
            
            # Add cluster size labels on clusters
            cluster_info = sample_clusters['cluster_info']
            for idx, (cid, size) in enumerate(top_5_clusters):
                if cid in cluster_info and len(cluster_info[cid]) > 0:
                    # Find center of cluster
                    positions = cluster_info[cid]
                    center_row = sum(p[0] for p in positions) / len(positions)
                    center_col = sum(p[1] for p in positions) / len(positions)
                    ax.text(center_col, center_row, str(size), ha='center', va='center',
                           fontsize=10, color='white', weight='bold',
                           bbox=dict(boxstyle='round', facecolor='black', alpha=0.5))
            
            fig.tight_layout()
            self.figures["mine_clusters"] = fig
        
        def save_to_pdf(self):
            """Save analytics results to PDF"""
            try:
                # Generate filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"minesweeper_analytics_{timestamp}.pdf"
                
                # Try to save in current directory
                filepath = os.path.join(os.getcwd(), filename)
                
                # Create PDF
                with PdfPages(filepath) as pdf:
                    # Page 1: Title and Configuration
                    fig = Figure(figsize=(8.5, 11))
                    fig.text(0.5, 0.9, "Minesweeper Analytics Report",
                            ha='center', va='top', fontsize=24, fontweight='bold')
                    
                    config = self.analytics_results['board_config']
                    n_boards = self.analytics_results['num_boards']
                    
                    config_text = (f"Configuration:\n"
                                 f"• Boards Generated: {n_boards}\n"
                                 f"• Board Size: {config['width']} x {config['height']}\n"
                                 f"• Mines per Board: {config['mines']}\n"
                                 f"• Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    fig.text(0.5, 0.7, config_text, ha='center', va='top', fontsize=14,
                            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
                    plt.axis('off')
                    pdf.savefig(fig, bbox_inches='tight')
                    plt.close(fig)
                    
                    # Add all charts in order
                    chart_order = ['heatmap', 'bar_chart', 'pie_chart', 'mine_clusters']
                    for key in chart_order:
                        if key in self.figures:
                            pdf.savefig(self.figures[key], bbox_inches='tight')
                
                # Show success message
                QMessageBox.information(None, "PDF Saved",
                                      f"All analytics charts saved to:\n{filepath}")
            except Exception as e:
                QMessageBox.warning(None, "PDF Save Error",
                                  f"Could not save PDF:\n{str(e)}")

except ImportError:
    # PyQt5 not available, create dummy class
    class AnalyticsDialog:
        def __init__(self, *args, **kwargs):
            raise ImportError("PyQt5 and matplotlib are required for analytics")

