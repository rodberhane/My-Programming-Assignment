"""
GUI Module
==========

This module provides the graphical user interface for the Minesweeper game using PyQt5.

User Manual:
------------
How to Play:
1. Click on a cell to reveal it. The first click is always safe!
2. Right-click (or long-press) on a cell to place/remove a flag
3. Numbers show how many mines are adjacent to that cell
4. Clear all non-mine cells to win!

Features:
- Three difficulty levels: Easy (9×9, 10 mines), Intermediate (16×16, 40 mines), Expert (30×16, 99 mines)
- Custom board sizes and mine counts
- Timer tracks your completion time
- Mine counter shows remaining unflagged mines
- Highscores: Your best times are saved automatically when you win
- Analytics: Generate statistical analysis of random board configurations

Controls:
- Left-click: Reveal cell
- Right-click: Toggle flag
- Reset button (🙂): Start a new game
- Analytics button: Open analytics dialog
- Leaderboard button: View top 10 scores for each difficulty
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QGridLayout, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QSpinBox,
                             QTabWidget, QScrollArea, QDialog, QInputDialog,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QMessageBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

from game_logic import MinesweeperLogic, CellState, GameState
from config import Difficulty, GameConfig
from highscores import get_highscores_manager


class CellButton(QPushButton):

    def __init__(self, row, col):
        super().__init__()
        self.row = row
        self.col = col
        self.setFixedSize(GameConfig.CELL_SIZE, GameConfig.CELL_SIZE)
        self.setFont(QFont('Arial', GameConfig.FONT_SIZE, QFont.Bold))
        self.set_unrevealed()
    
    def set_unrevealed(self):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {GameConfig.COLOR_UNREVEALED};
                border: 2px outset {GameConfig.COLOR_BORDER_LIGHT};
                font-size: {GameConfig.FONT_SIZE}px;
            }}
            QPushButton:hover {{
                background-color: #B0B0B0;
            }}
        """)
        self.setText('')
    
    def set_revealed(self, adjacent_mines):
        """Style for revealed cell"""
        color = "#000000"
        if adjacent_mines > 0:
            color = GameConfig.NUMBER_COLORS.get(adjacent_mines, '#000000')

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {GameConfig.COLOR_REVEALED};
                border: 1px solid {GameConfig.COLOR_BORDER_DARK};
                font-size: {GameConfig.FONT_SIZE}px;
                color: {color};
            }}
        """)

        self.setText(str(adjacent_mines) if adjacent_mines > 0 else '')

    
    def set_flagged(self):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {GameConfig.COLOR_UNREVEALED};
                border: 2px outset {GameConfig.COLOR_BORDER_LIGHT};
                color: {GameConfig.COLOR_FLAG};
                font-size: {GameConfig.FONT_SIZE}px;
            }}
        """)
        self.setText('🚩')
    
    def set_mine(self, exploded=False):
        """Style for mine cell"""
        bg_color = '#FF0000' if exploded else GameConfig.COLOR_REVEALED
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                border: 1px solid {GameConfig.COLOR_BORDER_DARK};
                font-size: {GameConfig.FONT_SIZE}px;
            }}
        """)
        self.setText('💣')


class DigitalDisplay(QLabel):
    """Digital display for mine counter and timer"""
    
    def __init__(self):
        super().__init__()
        self.setFont(QFont('Monospace', GameConfig.FONT_SIZE_DIGITAL, QFont.Bold))
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                background-color: #000000;
                color: #FF0000;
                border: 2px inset #808080;
                padding: 3px;
                min-width: 60px;
            }
        """)
        self.set_value(0)
    
    def set_value(self, value):
        """Set the display value"""
        value = max(-99, min(999, value))
        self.setText(f"{value:03d}")


class MinesweeperGUI(QMainWindow):
    """Main game window"""
    
    def __init__(self):
        super().__init__()
        self.game_logic = None
        self.cell_buttons = []
        self.timer_value = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.tab_widget = None
        
        self.init_ui()
        # Start with Beginner difficulty
        self.new_game(Difficulty.BEGINNER)
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle('Minesweeper')
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Difficulty tabs
        tab_widget = QTabWidget()
        tab_widget.setMaximumHeight(70)
        main_layout.addWidget(tab_widget)
        self.tab_widget = tab_widget
        
        # Create difficulty tabs
        for name, diff in [('Beginner', Difficulty.BEGINNER),
                          ('Intermediate', Difficulty.INTERMEDIATE),
                          ('Expert', Difficulty.EXPERT),
                          ('Custom', Difficulty.CUSTOM)]:
            tab = QWidget()
            
            if name == 'Custom':
                tab_layout = QHBoxLayout(tab)
                tab_layout.setContentsMargins(2, 2, 2, 2)
                
                # Width
                tab_layout.addWidget(QLabel('W:'))
                self.width_spin = QSpinBox()
                self.width_spin.setRange(GameConfig.MIN_WIDTH, GameConfig.MAX_WIDTH)
                self.width_spin.setValue(diff['width'])
                self.width_spin.setMaximumWidth(60)
                tab_layout.addWidget(self.width_spin)
                
                # Height
                tab_layout.addWidget(QLabel('H:'))
                self.height_spin = QSpinBox()
                self.height_spin.setRange(GameConfig.MIN_HEIGHT, GameConfig.MAX_HEIGHT)
                self.height_spin.setValue(diff['height'])
                self.height_spin.setMaximumWidth(60)
                tab_layout.addWidget(self.height_spin)
                
                # Mines
                tab_layout.addWidget(QLabel('M:'))
                self.mines_spin = QSpinBox()
                self.mines_spin.setRange(GameConfig.MIN_MINES, 999)
                self.mines_spin.setValue(diff['mines'])
                self.mines_spin.setMaximumWidth(60)
                tab_layout.addWidget(self.mines_spin)
                
                # Connect spinboxes to update game and validate mines
                self.width_spin.valueChanged.connect(self.update_custom_game)
                self.height_spin.valueChanged.connect(self.update_custom_game)
                self.mines_spin.valueChanged.connect(self.update_custom_game)
                
                tab_layout.addStretch()
            
            tab_widget.addTab(tab, name)
        
        # Connect tab change to start new game
        tab_widget.currentChanged.connect(lambda index: self.on_tab_changed(index))
        
        # Top panel (mine counter, reset button, timer) - Compact
        top_panel = QWidget()
        top_layout = QHBoxLayout(top_panel)
        top_layout.setContentsMargins(3, 3, 3, 3)
        
        # Mine counter
        self.mine_display = DigitalDisplay()
        top_layout.addWidget(self.mine_display)
        
        # Analytics button
        self.analytics_btn = QPushButton('Analytics')
        self.analytics_btn.setFixedHeight(28)
        self.analytics_btn.clicked.connect(self.open_analytics)
        top_layout.addWidget(self.analytics_btn)
        
        # Leaderboard button
        self.leaderboard_btn = QPushButton('Leaderboard')
        self.leaderboard_btn.setFixedHeight(28)
        self.leaderboard_btn.clicked.connect(self.open_leaderboard)
        top_layout.addWidget(self.leaderboard_btn)

        top_layout.addStretch()
        
        # Reset button
        self.reset_btn = QPushButton('🙂')
        self.reset_btn.setFont(QFont('Arial', GameConfig.BUTTON_FONT_SIZE))
        self.reset_btn.setFixedSize(40, 40)
        self.reset_btn.clicked.connect(self.reset_game)
        top_layout.addWidget(self.reset_btn)
        
        top_layout.addStretch()
        
        # Timer
        self.timer_display = DigitalDisplay()
        top_layout.addWidget(self.timer_display)
        
        main_layout.addWidget(top_panel)
        
        # Scroll area for game board
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Game board container
        self.board_container = QWidget()
        self.board_layout = QGridLayout(self.board_container)
        self.board_layout.setSpacing(0)
        self.board_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll_area.setWidget(self.board_container)
        main_layout.addWidget(scroll_area)
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2B2B2B;
            }
            QTabWidget::pane {
                border: 1px solid #888;
            }
            QTabBar::tab {
                padding: 3px 8px;
                margin: 1px;
            }
        """)
    
    def new_game(self, difficulty):
        """Start a new game with given difficulty"""
        # Stop timer
        self.timer.stop()
        self.timer_value = 0
        self.timer_display.set_value(0)
        
        # Create new game logic
        width = difficulty['width']
        height = difficulty['height']
        mines = min(difficulty['mines'], width * height - 9)  # Ensure enough space
        
        self.game_logic = MinesweeperLogic(width, height, mines)
        self.mine_display.set_value(self.game_logic.get_remaining_mines())
        
        # Clear old buttons
        for button in self.cell_buttons:
            button.deleteLater()
        self.cell_buttons.clear()
        
        # Create new board
        for row in range(height):
            for col in range(width):
                btn = CellButton(row, col)
                btn.clicked.connect(lambda checked, r=row, c=col: self.cell_left_click(r, c))
                btn.setContextMenuPolicy(Qt.CustomContextMenu)
                btn.customContextMenuRequested.connect(
                    lambda pos, r=row, c=col: self.cell_right_click(r, c))
                self.board_layout.addWidget(btn, row, col)
                self.cell_buttons.append(btn)
        
        # Reset UI
        self.reset_btn.setText('🙂')
        
        # Adjust window size to fit content better
        self.board_container.adjustSize()
        
        # Set reasonable max size based on screen
        max_width = 1200
        max_height = 800
        
        # Calculate required size
        board_width = width * GameConfig.CELL_SIZE + 50
        board_height = height * GameConfig.CELL_SIZE + 200
        
        # Set window size
        final_width = min(board_width, max_width)
        final_height = min(board_height, max_height)
        self.resize(final_width, final_height)
    
    def reset_game(self):
        """Reset the current game"""
        if self.game_logic:
            difficulty = {
                'width': self.game_logic.width,
                'height': self.game_logic.height,
                'mines': self.game_logic.total_mines
            }
            self.new_game(difficulty)
    
    def open_analytics(self):
        """Open the analytics dialog"""
        # Lazy import so missing plotting libs won't break startup
        try:
            from analytics import AnalyticsDialog
        except Exception as e:
            # Show error message if import failed
            QMessageBox.critical(
                self,
                "Analytics Error",
                f"Could not load analytics module:\n{str(e)}\n\n"
                "Please ensure matplotlib is installed:\npip install matplotlib"
            )
            return
        
        dlg = AnalyticsDialog(self)
        dlg.exec_()

    def on_tab_changed(self, index):
        """Handle tab change"""
        difficulties = [Difficulty.BEGINNER, Difficulty.INTERMEDIATE, 
                       Difficulty.EXPERT, Difficulty.CUSTOM]
        
        if index < len(difficulties):
            difficulty = difficulties[index]
            
            # For custom tab, use current spinbox values
            if index == 3:
                self.update_mines_max()
                difficulty = {
                    'width': self.width_spin.value(),
                    'height': self.height_spin.value(),
                    'mines': self.mines_spin.value()
                }
            
            self.new_game(difficulty)
    
    def update_custom_game(self):
        """Update game when custom settings change"""
        # Only update if custom tab is active
        if self.tab_widget.currentIndex() == 3:
            self.update_mines_max()
            difficulty = {
                'width': self.width_spin.value(),
                'height': self.height_spin.value(),
                'mines': self.mines_spin.value()
            }
            self.new_game(difficulty)
    
    def update_mines_max(self):
        """Update maximum allowed mines based on grid size"""
        max_mines = self.width_spin.value() * self.height_spin.value() - 9
        self.mines_spin.setMaximum(max_mines)
        # Clamp current value if it exceeds new maximum
        if self.mines_spin.value() > max_mines:
            self.mines_spin.setValue(max_mines)
    
    def cell_left_click(self, row, col):
        """Handle left click on a cell"""
        if self.game_logic.game_state in (GameState.WON, GameState.LOST):
            return
        
        # Start timer on first click
        if self.game_logic.game_state == GameState.NOT_STARTED:
            self.timer.start(1000)
        
        # Reveal cell
        revealed_cells = self.game_logic.reveal_cell(row, col)
        
        # Update UI for revealed cells
        for r, c in revealed_cells:
            btn = self.get_button(r, c)
            
            if self.game_logic.mines[r, c]:
                btn.set_mine(exploded=True)
            else:
                btn.set_revealed(int(self.game_logic.adjacent_counts[r, c]))
        
        # Check game state
        if self.game_logic.game_state == GameState.LOST:
            # Pass the coordinates of the exploded cell
            self.game_over(won=False, exploded_row=row, exploded_col=col) 
        elif self.game_logic.game_state == GameState.WON:
            self.game_over(won=True)
    
    def cell_right_click(self, row, col):
        """Handle right click on a cell (flag toggle)"""
        if self.game_logic.game_state in (GameState.WON, GameState.LOST):
            return
        
        if self.game_logic.toggle_flag(row, col):
            btn = self.get_button(row, col)
            
            if self.game_logic.cell_states[row, col] == CellState.FLAGGED:
                btn.set_flagged()
            else:
                btn.set_unrevealed()
            
            self.mine_display.set_value(self.game_logic.get_remaining_mines())
    
    def get_button(self, row, col):
        """Get button at given position"""
        idx = row * self.game_logic.width + col
        return self.cell_buttons[idx]
    
    def game_over(self, won, exploded_row=None, exploded_col=None):
        """
        Handle game over - update UI and save score if won.
        
        When the player wins, this method:
        1. Stops the timer
        2. Prompts for player name
        3. Saves the score to the leaderboard
        4. Updates the reset button to show victory
        """
        self.timer.stop()
        
        if won:
            self.reset_btn.setText('😎')
            # Prompt for player name and save score
            self.handle_win()
        else:
            self.reset_btn.setText('😵')
            # Reveal all mines
            mine_positions = self.game_logic.reveal_all_mines()
            for r, c in mine_positions:
                btn = self.get_button(r, c)
                if self.game_logic.cell_states[r, c] != CellState.FLAGGED:
                    is_exploded = (r == exploded_row and c == exploded_col)
                    # Use the passed coordinates
                    btn.set_mine(exploded=is_exploded)
    
    def handle_win(self):
        """
        Handle a win: prompt for player name and save score.
        
        This creates a simple dialog asking for the player's name,
        then saves their time to the leaderboard if it qualifies.
        """
        # Get player name
        name, ok = QInputDialog.getText(
            self, 
            "Congratulations!",
            f"You won in {self.timer_value} seconds!\n\nEnter your name:",
            text="Player"
        )
        
        if ok and name.strip():
            # Save score
            manager = get_highscores_manager()
            made_it = manager.save_score(
                name.strip(),
                self.timer_value,
                self.game_logic.width,
                self.game_logic.height,
                self.game_logic.total_mines
            )
            
            if made_it:
                QMessageBox.information(
                    self,
                    "High Score!",
                    f"Congratulations {name}!\n"
                    f"Your time of {self.timer_value} seconds made it to the leaderboard!"
                )
            else:
                QMessageBox.information(
                    self,
                    "Well Done!",
                    f"Great job, {name}!\n"
                    f"Your time: {self.timer_value} seconds"
                )
    
    def open_leaderboard(self):
        """Open the leaderboard dialog showing top 10 scores for each difficulty"""
        dialog = LeaderboardDialog(self)
        dialog.exec_()
    
    def update_timer(self):
        """Update the timer display"""
        if self.timer_value < GameConfig.MAX_TIME:
            self.timer_value += 1
            self.timer_display.set_value(self.timer_value)


class LeaderboardDialog(QDialog):
    """
    Dialog showing the top 10 scores for each difficulty level.
    
    This dialog displays leaderboards in a tabbed interface, with one tab
    for each difficulty (Easy, Intermediate, Expert, and any Custom configurations
    that have scores).
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Minesweeper Leaderboard")
        self.setMinimumSize(500, 400)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the leaderboard dialog UI"""
        layout = QVBoxLayout(self)
        
        # Create tab widget for different difficulties
        tab_widget = QTabWidget()
        
        manager = get_highscores_manager()
        all_leaderboards = manager.get_all_leaderboards()
        
        # Standard difficulties
        standard_diffs = [
            ("Easy", 9, 9, 10),
            ("Intermediate", 16, 16, 40),
            ("Expert", 30, 16, 99)
        ]
        
        for name, width, height, mines in standard_diffs:
            key = manager.get_difficulty_key(width, height, mines)
            scores = all_leaderboards.get(key, [])
            table = self.create_leaderboard_table(scores)
            tab_widget.addTab(table, name)
        
        # Custom difficulties
        for key, scores in all_leaderboards.items():
            if key.startswith("custom_"):
                name = manager.get_difficulty_name(key)
                table = self.create_leaderboard_table(scores)
                tab_widget.addTab(table, name)
        
        layout.addWidget(tab_widget)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
    
    def create_leaderboard_table(self, scores):
        """
        Create a table widget showing the leaderboard.
        
        Args:
            scores: List of HighscoreEntry objects
            
        Returns:
            QTableWidget populated with score data
        """
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Rank", "Name", "Time (seconds)", "Date"])
        table.horizontalHeader().setStretchLastSection(True)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setRowCount(max(10, len(scores)))
        
        # Populate table
        for i, entry in enumerate(scores[:10]):  # Top 10 only
            table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            table.setItem(i, 1, QTableWidgetItem(entry.name))
            table.setItem(i, 2, QTableWidgetItem(str(entry.time)))
            
            # Format date nicely
            try:
                from datetime import datetime
                date_obj = datetime.fromisoformat(entry.date)
                date_str = date_obj.strftime("%Y-%m-%d %H:%M")
            except:
                date_str = entry.date
            table.setItem(i, 3, QTableWidgetItem(date_str))
        
        # Fill empty rows
        for i in range(len(scores), 10):
            table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            table.setItem(i, 1, QTableWidgetItem("---"))
            table.setItem(i, 2, QTableWidgetItem("---"))
            table.setItem(i, 3, QTableWidgetItem("---"))
        
        table.resizeColumnsToContents()
        return table