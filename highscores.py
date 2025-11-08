"""
Highscores Module
================

This module manages the persistent leaderboard system for Minesweeper.
It stores the top 10 best times for each difficulty configuration (Easy, Intermediate, Expert, Custom).

How it works:
- Scores are saved to a JSON file (highscores.json) in the project directory
- Each difficulty has its own leaderboard with up to 10 entries
- When a player wins, they can enter their name and their time is recorded
- The leaderboard is automatically sorted by time (fastest first)

Key Functions:
- save_score(): Records a new score if it qualifies for the top 10
- get_leaderboard(): Retrieves the top 10 scores for a difficulty
- get_difficulty_key(): Converts game configuration to a unique key
"""

import json
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime


# File path for storing highscores
HIGHSCORES_FILE = os.path.join(os.path.dirname(__file__), 'highscores.json')


class HighscoreEntry:
    """
    Represents a single highscore entry.
    
    Attributes:
        name: Player's name
        time: Time taken in seconds
        date: Date when the score was achieved (ISO format string)
    """
    
    def __init__(self, name: str, time: int, date: Optional[str] = None):
        self.name = name
        self.time = time
        self.date = date or datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert entry to dictionary for JSON storage"""
        return {
            'name': self.name,
            'time': self.time,
            'date': self.date
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'HighscoreEntry':
        """Create entry from dictionary loaded from JSON"""
        return cls(
            name=data.get('name', 'Unknown'),
            time=data.get('time', 999),
            date=data.get('date', datetime.now().isoformat())
        )
    
    def __lt__(self, other):
        """Comparison for sorting (lower time is better)"""
        return self.time < other.time


class HighscoresManager:
    """
    Manages the persistent highscores system.
    
    This class handles loading, saving, and querying highscore data.
    It maintains separate leaderboards for each difficulty configuration.
    """
    
    def __init__(self):
        """Initialize the highscores manager and load existing data"""
        self.scores: Dict[str, List[HighscoreEntry]] = {}
        self.load_scores()
    
    def get_difficulty_key(self, width: int, height: int, mines: int) -> str:
        """
        Generate a unique key for a difficulty configuration.
        
        This converts the game parameters into a string that identifies
        the difficulty level. Standard configurations get friendly names,
        while custom configurations get a descriptive key.
        
        Args:
            width: Board width
            height: Board height
            mines: Number of mines
            
        Returns:
            A string key identifying the difficulty (e.g., "easy", "intermediate", "expert", "custom_30x16_99")
        """
        # Standard difficulty presets
        if width == 9 and height == 9 and mines == 10:
            return "easy"
        elif width == 16 and height == 16 and mines == 40:
            return "intermediate"
        elif width == 30 and height == 16 and mines == 99:
            return "expert"
        else:
            # Custom configuration
            return f"custom_{width}x{height}_{mines}"
    
    def get_difficulty_name(self, key: str) -> str:
        """
        Get a human-readable name for a difficulty key.
        
        Args:
            key: The difficulty key
            
        Returns:
            A friendly name like "Easy", "Intermediate", "Expert", or "Custom (30x16, 99 mines)"
        """
        if key == "easy":
            return "Easy (9×9, 10 mines)"
        elif key == "intermediate":
            return "Intermediate (16×16, 40 mines)"
        elif key == "expert":
            return "Expert (30×16, 99 mines)"
        elif key.startswith("custom_"):
            # Parse custom key: "custom_30x16_99"
            parts = key.replace("custom_", "").split("_")
            if len(parts) >= 2:
                size = parts[0]  # "30x16"
                mines = parts[1]  # "99"
                return f"Custom ({size}, {mines} mines)"
        return key
    
    def load_scores(self):
        """
        Load highscores from the JSON file.
        
        If the file doesn't exist or is corrupted, it starts with empty leaderboards.
        This method is called automatically when the manager is created.
        """
        if os.path.exists(HIGHSCORES_FILE):
            try:
                with open(HIGHSCORES_FILE, 'r') as f:
                    data = json.load(f)
                
                # Convert loaded data back to HighscoreEntry objects
                self.scores = {}
                for key, entries in data.items():
                    self.scores[key] = [
                        HighscoreEntry.from_dict(entry) for entry in entries
                    ]
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                # If file is corrupted, start fresh
                print(f"Warning: Could not load highscores: {e}")
                self.scores = {}
        else:
            self.scores = {}
    
    def save_scores(self):
        """
        Save highscores to the JSON file.
        
        This writes all current leaderboard data to disk. It's called
        automatically whenever scores are updated.
        """
        # Convert entries to dictionaries
        data = {}
        for key, entries in self.scores.items():
            data[key] = [entry.to_dict() for entry in entries]
        
        try:
            with open(HIGHSCORES_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            print(f"Error: Could not save highscores: {e}")
    
    def save_score(self, name: str, time: int, width: int, height: int, mines: int) -> bool:
        """
        Save a new score if it qualifies for the top 10.
        
        This method checks if the new score is good enough to make it into
        the leaderboard. If there are fewer than 10 scores, it's automatically
        added. Otherwise, it's only added if it's faster than the slowest
        existing score.
        
        Args:
            name: Player's name
            time: Time taken in seconds
            width: Board width
            height: Board height
            mines: Number of mines
            
        Returns:
            True if the score was added to the leaderboard, False otherwise
        """
        key = self.get_difficulty_key(width, height, mines)
        
        # Get or create leaderboard for this difficulty
        if key not in self.scores:
            self.scores[key] = []
        
        # Create new entry
        new_entry = HighscoreEntry(name, time)
        
        # Add to list
        self.scores[key].append(new_entry)
        
        # Sort by time (fastest first) and keep only top 10
        self.scores[key].sort()
        self.scores[key] = self.scores[key][:10]
        
        # Check if the new entry made it into the top 10
        made_it = new_entry in self.scores[key]
        
        # Save to file
        self.save_scores()
        
        return made_it
    
    def get_leaderboard(self, width: int, height: int, mines: int) -> List[HighscoreEntry]:
        """
        Get the top 10 scores for a specific difficulty.
        
        Args:
            width: Board width
            height: Board height
            mines: Number of mines
            
        Returns:
            A list of HighscoreEntry objects, sorted by time (fastest first)
        """
        key = self.get_difficulty_key(width, height, mines)
        return self.scores.get(key, [])
    
    def get_all_leaderboards(self) -> Dict[str, List[HighscoreEntry]]:
        """
        Get all leaderboards for all difficulties.
        
        Returns:
            A dictionary mapping difficulty keys to their leaderboard lists
        """
        return self.scores.copy()


# Global instance for easy access
_highscores_manager = None


def get_highscores_manager() -> HighscoresManager:
    """
    Get the global highscores manager instance.
    
    This function provides a singleton pattern - there's only one
    highscores manager throughout the application, ensuring consistency.
    
    Returns:
        The global HighscoresManager instance
    """
    global _highscores_manager
    if _highscores_manager is None:
        _highscores_manager = HighscoresManager()
    return _highscores_manager

