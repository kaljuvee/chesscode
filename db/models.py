"""Pydantic models for database entities."""
from datetime import date, datetime
from typing import Optional, List, Dict

from pydantic import BaseModel


class Game(BaseModel):
    """A chess game from a PGN database."""
    id: Optional[int] = None
    source_file: str = ""
    event: Optional[str] = None
    site: Optional[str] = None
    date: Optional[date] = None
    white: str = ""
    black: str = ""
    result: Optional[str] = None
    white_elo: Optional[int] = None
    black_elo: Optional[int] = None
    eco: Optional[str] = None
    pgn_text: str = ""
    moves_san: Optional[str] = None
    move_count: Optional[int] = None


class GameLabel(BaseModel):
    """A label or mask attached to a game or specific position."""
    id: Optional[int] = None
    game_id: int
    label_type: str          # e.g. "nag", "comment", "opening", "theme", "mask"
    label_value: str         # e.g. "$1", "Brilliant move", "Sicilian Defense"
    position_fen: Optional[str] = None  # FEN of the specific position (None = whole game)
    move_number: Optional[int] = None   # Half-move number (None = whole game)
    created_by: Optional[str] = None    # "admin", "engine", "auto"


class PlayerStats(BaseModel):
    """Cached statistics for a player."""
    player_name: str
    total_games: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    avg_cpl: Optional[float] = None
    blunder_rate: Optional[float] = None
    t1_accuracy: Optional[float] = None
    most_played_eco: Optional[str] = None
    analyzed_at: Optional[datetime] = None


class StudentProfile(BaseModel):
    """A student profile for the personal teacher agent."""
    id: Optional[int] = None
    username: str
    estimated_rating: Optional[int] = None
    weaknesses: Optional[Dict] = None
    last_assessed: Optional[datetime] = None


class BookChapter(BaseModel):
    """A chapter from a teaching book (for children's coach)."""
    id: Optional[int] = None
    book_title: Optional[str] = None
    chapter_number: Optional[int] = None
    chapter_title: Optional[str] = None
    content: Optional[str] = None
    difficulty_level: int = 1   # 1=beginner, 2=intermediate, 3=advanced
    topics: Optional[List[str]] = None
