"""
Minesweeper Game - Main Entry Point
====================================

User Manual:
------------
How to Run:
1. Install dependencies: pip install -r requirements.txt
2. Run the game: python minesweeper.py
   Or use the startup script: ./start_minesweeper.sh

Game Flow (UML-like Overview):
==============================
┌─────────────────────────────────────────────────────────────┐
│                    GAME START                                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 1. Application Initialization                         │   │
│  │    - Load PyQt5 GUI framework                        │   │
│  │    - Create main window                              │   │
│  │    - Initialize game with default difficulty         │   │
│  └──────────────────────────────────────────────────────┘   │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 2. GAMEPLAY                                           │   │
│  │    - Player clicks cells to reveal them               │   │
│  │    - First click triggers mine placement             │   │
│  │    - Timer starts on first click                     │   │
│  │    - Right-click to flag/unflag cells                │   │
│  │    - Game tracks revealed cells and flags            │   │
│  └──────────────────────────────────────────────────────┘   │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 3. WIN/LOSE DETECTION                                 │   │
│  │    - WIN: All non-mine cells revealed                │   │
│  │      → Prompt for player name                        │   │
│  │      → Save score to leaderboard                      │   │
│  │      → Show congratulations message                  │   │
│  │    - LOSE: Mine clicked                              │   │
│  │      → Reveal all mines                              │   │
│  │      → Show game over message                        │   │
│  └──────────────────────────────────────────────────────┘   │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 4. ANALYTICS (Optional)                               │   │
│  │    - Click "Analytics" button                        │   │
│  │    - Configure board parameters                       │   │
│  │    - Generate multiple random boards                  │   │
│  │    - Compute statistics and visualizations            │   │
│  │    - Save results as PDF                              │   │
│  └──────────────────────────────────────────────────────┘   │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 5. EXIT                                               │   │
│  │    - Close window or quit application                │   │
│  │    - Highscores are automatically saved              │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘

Module Structure:
-----------------
- minesweeper.py: Main entry point (this file)
- game_logic.py: Core game rules and state management
- gui.py: Graphical user interface (PyQt5)
- analytics.py: Statistical analysis and visualization
- highscores.py: Leaderboard management
- config.py: Game configuration and constants

Dependencies:
-------------
- PyQt5: GUI framework
- numpy: Efficient array operations
- matplotlib: Plotting and visualization (for analytics)
"""

import sys
from PyQt5.QtWidgets import QApplication
from gui import MinesweeperGUI


def main():
    """
    Main entry point for the Minesweeper application.
    
    This function:
    1. Creates the Qt application
    2. Sets the application style
    3. Creates and shows the main game window
    4. Starts the event loop
    
    The application runs until the user closes the window.
    """
    app = QApplication(sys.argv)
    
    # Use Fusion style for a modern, consistent look
    app.setStyle('Fusion')
    
    # Create and show main window
    game = MinesweeperGUI()
    game.show()
    
    # Run application event loop (blocks until window is closed)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()