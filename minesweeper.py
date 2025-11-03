import sys
from PyQt5.QtWidgets import QApplication
from gui import MinesweeperGUI


def main():
    app = QApplication(sys.argv)
    
    app.setStyle('Fusion')
    
    # Create and show main window
    game = MinesweeperGUI()
    game.show()
    
    # Run application
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()