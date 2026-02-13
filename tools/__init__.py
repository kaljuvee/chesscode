"""Shared tools package for chess agents."""
from .board_tools import (
    analyze_position,
    suggest_move,
    explain_move,
    get_game_phase,
    get_legal_moves,
)

__all__ = [
    'analyze_position',
    'suggest_move',
    'explain_move',
    'get_game_phase',
    'get_legal_moves',
]
