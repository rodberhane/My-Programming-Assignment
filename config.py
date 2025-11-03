"""
Minesweeper Game Configuration
Contains difficulty presets and game constants
"""

class Difficulty:
    """Difficulty presets for the game"""
    BEGINNER = {
        'width': 9,
        'height': 9,
        'mines': 10
    }
    
    INTERMEDIATE = {
        'width': 16,
        'height': 16,
        'mines': 40
    }
    
    EXPERT = {
        'width': 30,
        'height': 16,
        'mines': 99
    }
    
    CUSTOM = {
        'width': 30,
        'height': 30,
        'mines': 150
    }

class GameConfig:
    """Game configuration and constants"""
    CELL_SIZE = 25
    BORDER_WIDTH = 8
    TOP_PANEL_HEIGHT = 45
    FONT_SIZE = 10
    FONT_SIZE_DIGITAL = 20
    BUTTON_FONT_SIZE = 16
    
    # Colors
    COLOR_UNREVEALED = '#3A3A3A'
    COLOR_REVEALED = '#1E1E1E'
    COLOR_MINE = '#8B0000'
    COLOR_FLAG = '#FF4500'
    COLOR_BORDER_LIGHT = '#4A4A4A'
    COLOR_BORDER_DARK = '#0A0A0A'
    COLOR_BACKGROUND = '#2B2B2B'
    
    # Number colors
    NUMBER_COLORS = {
        1: '#5B9BD5',
        2: '#70AD47',
        3: '#FF6B6B',
        4: '#9370DB',
        5: '#FFA500',
        6: '#20B2AA',
        7: '#FFD700',
        8: '#C0C0C0'
    }
    
    # Timer
    MAX_TIME = 999
    
    # Custom game limits
    MIN_WIDTH = 5
    MAX_WIDTH = 50
    MIN_HEIGHT = 5
    MAX_HEIGHT = 50
    MIN_MINES = 1