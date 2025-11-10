"""
Highscores Module
=================
Manages leaderboard/highscore functionality for Minesweeper.
Stores scores in JSON format and provides methods to save/retrieve scores.
"""
import json
import os
from typing import List, Dict, Optional
from datetime import datetime

# Path to highscore JSON file
HIGHSCORE_FILE = os.path.join(os.path.dirname(__file__), 'highscore.json')


class HighscoreEntry:
    """Represents a single highscore entry"""
    
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
        """Less than comparison for sorting (lower time is better)"""
        return self.time < other.time


class HighscoresManager:
    """Manages all highscores for different difficulty levels"""
    
    def __init__(self):
        self.scores: Dict[str, List[HighscoreEntry]] = {}
        self.load_scores()
    
    def get_difficulty_key(self, width: int, height: int, mines: int) -> str:
        """Get the key for a difficulty configuration"""
        if width == 9 and height == 9 and mines == 10:
            return "easy"
        elif width == 16 and height == 16 and mines == 40:
            return "intermediate"
        elif width == 30 and height == 16 and mines == 99:
            return "expert"
        else:
            return f"custom_{width}x{height}_{mines}"
    
    def get_difficulty_name(self, key: str) -> str:
        """Get display name for a difficulty key"""
        if key == "easy":
            return "Easy (9x9, 10 mines)"
        elif key == "intermediate":
            return "Intermediate (16x16, 40 mines)"
        elif key == "expert":
            return "Expert (30x16, 99 mines)"
        elif key.startswith("custom_"):
            # Parse custom key: "custom_30x16_99"
            parts = key.replace("custom_", "").split("_")
            if len(parts) >= 2:
                size = parts[0]  # "30x16"
                mines = parts[1]  # "99"
                return f"Custom ({size}, {mines} mines)"
            return key
        return key
    
    def load_scores(self):
        """Load scores from JSON file"""
        if os.path.exists(HIGHSCORE_FILE):
            try:
                with open(HIGHSCORE_FILE, 'r') as f:
                    data = json.load(f)
                self.scores = {}
                for key, entries in data.items():
                    self.scores[key] = [HighscoreEntry.from_dict(entry) for entry in entries]
                    # Sort entries by time (best first)
                    self.scores[key].sort()
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                # If file is corrupted, start fresh
                print(f"Warning: Could not load highscores: {e}")
                self.scores = {}
        else:
            self.scores = {}
    
    def save_scores(self):
        """Save scores to JSON file"""
        try:
            data = {}
            for key, entries in self.scores.items():
                data[key] = [entry.to_dict() for entry in entries]
            
            with open(HIGHSCORE_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving highscores: {e}")
    
    def save_score(self, name: str, time: int, width: int, height: int, mines: int) -> bool:
        """
        Save a score for the given difficulty.
        Returns True if the score made it to the top 10, False otherwise.
        """
        key = self.get_difficulty_key(width, height, mines)
        
        # Get or create list for this difficulty
        if key not in self.scores:
            self.scores[key] = []
        
        # Create new entry
        entry = HighscoreEntry(name, time)
        
        # Add entry and sort
        self.scores[key].append(entry)
        self.scores[key].sort()
        
        # Keep only top 10
        self.scores[key] = self.scores[key][:10]
        
        # Check if this score made it to top 10
        made_it = entry in self.scores[key]
        
        # Save to file
        self.save_scores()
        
        return made_it
    
    def get_all_leaderboards(self) -> Dict[str, List[HighscoreEntry]]:
        """Get all leaderboards as a dictionary"""
        return self.scores.copy()


# Singleton instance
_manager_instance: Optional[HighscoresManager] = None


def get_highscores_manager() -> HighscoresManager:
    """Get the singleton highscores manager instance"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = HighscoresManager()
    return _manager_instance
