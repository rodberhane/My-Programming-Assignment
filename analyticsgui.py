"""
Analytics GUI for Minesweeper
Allows users to configure board parameters and generate analytics visualizations
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
from analytics import generate_boards, run_all_analytics


class AnalyticsGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Minesweeper Analytics")
        self.root.geometry("1200x800")
        
        # Analytics results
        self.analytics_results = None
        self.boards = []
        self.figures = {}  # Store figures for PDF export
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Configuration panel (left side)
        config_frame = ttk.LabelFrame(main_frame, text="Board Configuration", padding="10")
        config_frame.grid(row=0, column=0, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Number of boards
        ttk.Label(config_frame, text="Number of boards (n):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.n_boards_var = tk.IntVar(value=100)
        n_spin = ttk.Spinbox(config_frame, from_=1, to=10000, textvariable=self.n_boards_var, width=15)
        n_spin.grid(row=0, column=1, pady=5, padx=5)
        
        # Difficulty selection
        ttk.Label(config_frame, text="Difficulty:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.difficulty_var = tk.StringVar(value="Beginner")
        difficulty_combo = ttk.Combobox(config_frame, textvariable=self.difficulty_var, 
                                        values=["Beginner", "Intermediate", "Expert", "Custom"],
                                        state="readonly", width=12)
        difficulty_combo.grid(row=1, column=1, pady=5, padx=5)
        difficulty_combo.bind("<<ComboboxSelected>>", self.on_difficulty_change)
        
        # Custom configuration (initially hidden)
        self.custom_frame = ttk.LabelFrame(config_frame, text="Custom Configuration", padding="5")
        
        ttk.Label(self.custom_frame, text="Width:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.width_var = tk.IntVar(value=30)
        width_spin = ttk.Spinbox(self.custom_frame, from_=5, to=50, textvariable=self.width_var, width=10)
        width_spin.grid(row=0, column=1, pady=2, padx=2)
        
        ttk.Label(self.custom_frame, text="Height:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.height_var = tk.IntVar(value=30)
        height_spin = ttk.Spinbox(self.custom_frame, from_=5, to=50, textvariable=self.height_var, width=10)
        height_spin.grid(row=1, column=1, pady=2, padx=2)
        
        ttk.Label(self.custom_frame, text="Mines:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.mines_var = tk.IntVar(value=150)
        mines_spin = ttk.Spinbox(self.custom_frame, from_=1, to=1000, textvariable=self.mines_var, width=10)
        mines_spin.grid(row=2, column=1, pady=2, padx=2)
        
        # Generate button
        generate_btn = ttk.Button(config_frame, text="Generate Analytics", command=self.generate_analytics)
        generate_btn.grid(row=3, column=0, columnspan=2, pady=20, sticky=(tk.W, tk.E))
        
        # Export PDF button
        export_btn = ttk.Button(config_frame, text="Export to PDF", command=self.export_to_pdf, state=tk.DISABLED)
        export_btn.grid(row=4, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        self.export_btn = export_btn
        
        # Results panel (right side)
        results_frame = ttk.LabelFrame(main_frame, text="Analytics Results", padding="10")
        results_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # Canvas with scrollbar for results
        canvas_frame = ttk.Frame(results_frame)
        canvas_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        canvas_frame.columnconfigure(0, weight=1)
        canvas_frame.rowconfigure(0, weight=1)
        
        self.canvas = tk.Canvas(canvas_frame)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        self.results_container = self.scrollable_frame
    
    def on_difficulty_change(self, event=None):
        """Handle difficulty selection change"""
        difficulty = self.difficulty_var.get()
        
        if difficulty == "Custom":
            self.custom_frame.grid(row=2, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        else:
            self.custom_frame.grid_remove()
    
    def get_board_config(self):
        """Get board configuration based on selected difficulty"""
        difficulty = self.difficulty_var.get()
        
        if difficulty == "Beginner":
            return 9, 9, 10
        elif difficulty == "Intermediate":
            return 16, 16, 40
        elif difficulty == "Expert":
            return 30, 16, 99
        else:  # Custom
            return self.width_var.get(), self.height_var.get(), self.mines_var.get()
    
    def generate_analytics(self):
        """Generate boards and run analytics"""
        try:
            n = self.n_boards_var.get()
            width, height, mines = self.get_board_config()
            
            # Validate configuration
            max_mines = width * height - 9  # At least 9 cells must be safe for first click
            if mines > max_mines:
                messagebox.showerror("Error", f"Too many mines! Maximum: {max_mines}")
                return
            
            # Show progress
            self.root.config(cursor="wait")
            self.root.update()
            
            # Generate boards
            self.boards = generate_boards(n, width, height, mines)
            
            # Run analytics
            self.analytics_results = run_all_analytics(self.boards)
            
            # Display results
            self.display_results()
            
            # Enable export button
            self.export_btn.config(state=tk.NORMAL)
            
            self.root.config(cursor="")
            messagebox.showinfo("Success", f"Generated {n} boards and computed analytics!")
            
        except Exception as e:
            self.root.config(cursor="")
            messagebox.showerror("Error", f"Failed to generate analytics: {str(e)}")
    
    def display_results(self):
        """Display analytics results in the GUI"""
        # Clear previous results
        for widget in self.results_container.winfo_children():
            widget.destroy()
        
        if not self.analytics_results:
            return
        
        results = self.analytics_results
        
        # 1. Cell Distribution by Adjacent Mine Count (Bar Chart)
        cell_numbers = results['cell_numbers']
        numbers = list(cell_numbers.keys())
        counts = list(cell_numbers.values())
        
        # Color scheme matching the example
        colors = ['#5B9BD5', '#70AD47', '#FF6B6B', '#9370DB', '#FFA500', 
                 '#20B2AA', '#FFD700', '#C0C0C0', '#808080']
        
        fig, ax = plt.subplots(figsize=(8, 5))
        bars = ax.bar(numbers, counts, color=colors[:len(numbers)], edgecolor='black', linewidth=1.5)
        ax.set_xlabel("Number of Adjacent Mines", fontsize=12)
        ax.set_ylabel("Cell Count", fontsize=12)
        ax.set_title("Cell Distribution by Adjacent Mine Count", fontsize=14, fontweight='bold')
        ax.set_xticks(numbers)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{int(height)}',
                       ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        self.add_figure_to_gui(fig, "cell_numbers")
        
        # 2. White vs Numbered Cells (Pie Chart)
        white_vs_numbered = results['white_vs_numbered']
        white_count = white_vs_numbered['white']
        numbered_count = white_vs_numbered['numbered']
        total = white_count + numbered_count
        
        fig, ax = plt.subplots(figsize=(8, 5))
        sizes = [white_count, numbered_count]
        labels = ['White Cells', 'Numbered Cells']
        colors_pie = ['#5B9BD5', '#FF6B6B']
        explode = (0.05, 0.05)
        
        wedges, texts, autotexts = ax.pie(sizes, explode=explode, labels=labels, colors=colors_pie,
                                          autopct=lambda pct: f'{pct:.1f}%\n({int(pct/100*total)} cells)',
                                          shadow=True, startangle=90, textprops={'fontsize': 11})
        
        ax.set_title("White vs Numbered Cells", fontsize=14, fontweight='bold', pad=20)
        plt.tight_layout()
        self.add_figure_to_gui(fig, "white_vs_numbered")
        
        # 3. Mine Clusters Visualization
        if results.get('sample_clusters'):
            self.create_cluster_visualization(results['sample_clusters'])
        
        # 4. Mine Neighborhood Heatmap with mine markers
        self.create_heatmap_with_mines(results['heatmap'], results.get('sample_clusters'))
        
        # 5. White cells histogram (keep for completeness)
        self.create_histogram(
            results['white_cells'],
            "Number of White Cells per Board",
            "Number of White Cells",
            "Frequency",
            "white_cells"
        )
        
        # 6. Mine clusters histogram (keep for completeness)
        self.create_histogram(
            results['mine_clusters'],
            "Number of Mine Clusters per Board",
            "Number of Clusters",
            "Frequency",
            "mine_clusters"
        )
    
    def create_histogram(self, data, title, xlabel, ylabel, key):
        """Create and add a histogram to the GUI"""
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.hist(data, bins=min(50, len(np.unique(data))), color='steelblue', edgecolor='black', alpha=0.7)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        
        self.add_figure_to_gui(fig, key)
    
    def create_cluster_visualization(self, cluster_data):
        """Create mine clusters visualization"""
        if not cluster_data:
            return
        
        board = cluster_data['board']
        cluster_map = cluster_data['cluster_map']
        cluster_sizes = cluster_data['cluster_sizes']
        num_clusters = cluster_data['num_clusters']
        isolated_mines = cluster_data['isolated_mines']
        largest_size = cluster_data['largest_cluster_size']
        
        height, width = cluster_map.shape
        
        # Separate clusters from isolated mines (size 1)
        clusters_only = [(cid, size) for cid, size in cluster_sizes.items() if size > 1]
        isolated = [(cid, size) for cid, size in cluster_sizes.items() if size == 1]
        
        # Get top 5 largest clusters (excluding isolated)
        sorted_clusters = sorted(clusters_only, key=lambda x: x[1], reverse=True)
        top_5_clusters = sorted_clusters[:5]
        
        # Color palette for clusters
        cluster_colors = {
            -1: [0.2, 0.2, 0.2],  # Dark grey for non-mines (RGB)
        }
        
        # Assign colors to top clusters
        top_colors = ['#1f77b4', '#aec7e8', '#ff7f0e', '#9467bd', '#2ca02c']  # Blue, light blue, orange, purple, green
        for idx, (cid, size) in enumerate(top_5_clusters):
            color = top_colors[idx].lstrip('#')
            rgb = tuple(int(color[i:i+2], 16)/255.0 for i in (0, 2, 4))
            cluster_colors[cid] = rgb
        
        # Assign colors to other clusters (size > 1)
        other_colors = ['#d62728', '#ff9896', '#c5b0d5', '#c49c94', '#f7b6d3', '#dbdb8d', '#9edae5']
        other_idx = 0
        for cid, size in sorted_clusters[5:]:
            color = other_colors[other_idx % len(other_colors)].lstrip('#')
            rgb = tuple(int(color[i:i+2], 16)/255.0 for i in (0, 2, 4))
            cluster_colors[cid] = rgb
            other_idx += 1
        
        # Isolated mines are white
        for cid, size in isolated:
            cluster_colors[cid] = [1.0, 1.0, 1.0]  # White for isolated mines
        
        # Create visualization
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Create color map
        vis_array = np.zeros((height, width, 3))
        for row in range(height):
            for col in range(width):
                cid = cluster_map[row, col]
                if cid == -1:
                    vis_array[row, col] = cluster_colors[-1]  # Dark grey for non-mines
                elif cid in cluster_colors:
                    vis_array[row, col] = cluster_colors[cid]
                else:
                    vis_array[row, col] = [1.0, 1.0, 1.0]  # White fallback
        
        ax.imshow(vis_array, aspect='auto', origin='upper')
        ax.set_title(f"Mine Clusters Analysis\n{num_clusters} clusters, {isolated_mines} isolated mines, Largest cluster: {largest_size} mines",
                    fontsize=14, fontweight='bold', pad=15)
        ax.set_xlabel("Column", fontsize=11)
        ax.set_ylabel("Row", fontsize=11)
        
        # Add legend
        legend_elements = []
        for idx, (cid, size) in enumerate(top_5_clusters):
            color = top_colors[idx]
            legend_elements.append(plt.Rectangle((0,0),1,1, facecolor=color, edgecolor='black', label=f'Cluster {idx+1} ({size} mines)'))
        legend_elements.append(plt.Rectangle((0,0),1,1, facecolor='white', edgecolor='black', label='Isolated mines'))
        
        ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.15, 1))
        
        plt.tight_layout()
        self.add_figure_to_gui(fig, "mine_clusters_vis")
    
    def create_heatmap_with_mines(self, heatmap, cluster_data):
        """Create heatmap with mine locations marked"""
        if heatmap.size == 0:
            return
        
        height, width = heatmap.shape
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Create heatmap
        im = ax.imshow(heatmap, cmap='RdYlBu_r', interpolation='nearest', aspect='auto', origin='upper')
        
        # Get mine positions from sample board if available
        if cluster_data and cluster_data.get('board'):
            mines = cluster_data['board']['mines']
            mine_positions = np.argwhere(mines)
            
            # Mark mine locations with stars
            for row, col in mine_positions:
                ax.text(col, row, '☆', ha='center', va='center', 
                       fontsize=12, color='white', weight='bold',
                       bbox=dict(boxstyle='circle', facecolor='none', edgecolor='none'))
        
        config = self.analytics_results['board_config']
        ax.set_title(f"Mine Neighborhood Heatmap\n{config['width']}x{config['height']} Board, {config['mines']} Mines",
                    fontsize=14, fontweight='bold', pad=15)
        ax.set_xlabel("Column", fontsize=11)
        ax.set_ylabel("Row", fontsize=11)
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax, label="Adjacent Mines", shrink=0.8)
        cbar.ax.tick_params(labelsize=9)
        
        # Add legend for mines
        if cluster_data and cluster_data.get('board'):
            from matplotlib.patches import Patch
            legend_elements = [plt.Line2D([0], [0], marker='*', color='w', 
                                         markerfacecolor='white', markersize=12, 
                                         markeredgecolor='black', markeredgewidth=1,
                                         label='☆ Mines', linestyle='None')]
            ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.15, 0.95))
        
        plt.tight_layout()
        self.add_figure_to_gui(fig, "heatmap")
    
    def add_figure_to_gui(self, fig, key):
        """Add a matplotlib figure to the GUI"""
        canvas = FigureCanvasTkAgg(fig, self.results_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Store figure for PDF export
        self.figures[key] = fig
    
    def export_to_pdf(self):
        """Export analytics results to PDF using matplotlib"""
        if not self.analytics_results:
            messagebox.showwarning("Warning", "No analytics results to export!")
            return
        
        # Ask for file location
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if not filename:
            return
        
        try:
            # Create PDF using matplotlib's PdfPages
            with PdfPages(filename) as pdf:
                # Page 1: Title and Configuration
                fig = plt.figure(figsize=(8.5, 11))  # Letter size
                fig.text(0.5, 0.9, "Minesweeper Analytics Report", 
                        ha='center', va='top', fontsize=24, fontweight='bold', color='darkblue')
                
                # Configuration info
                config = self.analytics_results['board_config']
                n_boards = self.analytics_results['num_boards']
                
                config_text = f"""
Configuration:
• Boards Generated: {n_boards}
• Board Size: {config['width']} x {config['height']}
• Mines per Board: {config['mines']}
                """
                
                fig.text(0.5, 0.7, config_text, 
                        ha='center', va='top', fontsize=14, 
                        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
                
                plt.axis('off')
                pdf.savefig(fig, bbox_inches='tight')
                plt.close(fig)
                
                # Page 2: Cell Distribution by Adjacent Mine Count
                if 'cell_numbers' in self.figures:
                    fig = self.figures['cell_numbers']
                    pdf.savefig(fig, bbox_inches='tight')
                
                # Page 3: White vs Numbered Cells (Pie Chart)
                if 'white_vs_numbered' in self.figures:
                    fig = self.figures['white_vs_numbered']
                    pdf.savefig(fig, bbox_inches='tight')
                
                # Page 4: Mine Clusters Visualization
                if 'mine_clusters_vis' in self.figures:
                    fig = self.figures['mine_clusters_vis']
                    pdf.savefig(fig, bbox_inches='tight')
                
                # Page 5: Mine Neighborhood Heatmap
                if 'heatmap' in self.figures:
                    fig = self.figures['heatmap']
                    pdf.savefig(fig, bbox_inches='tight')
                
                # Page 6: White cells histogram (additional)
                if 'white_cells' in self.figures:
                    fig = self.figures['white_cells']
                    pdf.savefig(fig, bbox_inches='tight')
                
                # Page 7: Mine clusters histogram (additional)
                if 'mine_clusters' in self.figures:
                    fig = self.figures['mine_clusters']
                    pdf.savefig(fig, bbox_inches='tight')
            
            messagebox.showinfo("Success", f"PDF exported successfully to:\n{filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export PDF: {str(e)}")


def main():
    root = tk.Tk()
    app = AnalyticsGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

