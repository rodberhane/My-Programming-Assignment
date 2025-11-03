from PyQt5.QtWidgets import (QMainWindow, QWidget, QGridLayout, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QSpinBox,
                             QTabWidget, QScrollArea)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

from game_logic import MinesweeperLogic, CellState, GameState
from config import Difficulty, GameConfig


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
        """Handle game over"""
        self.timer.stop()
        
        if won:
            self.reset_btn.setText('😎')
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
    
    def update_timer(self):
        """Update the timer display"""
        if self.timer_value < GameConfig.MAX_TIME:
            self.timer_value += 1
            self.timer_display.set_value(self.timer_value)