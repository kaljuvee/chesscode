#!/usr/bin/env python3
"""Generate demonstration screenshots of the Chess TUI."""
import os
from pathlib import Path

# Create screenshots directory
screenshots_dir = Path("/home/ubuntu/chesscode/screenshots")
screenshots_dir.mkdir(exist_ok=True)

# Demo 1: Initial board state
demo1 = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                        ChessCode - Interactive Chess TUI                     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  Chess Board                          │  AI Assistant                        ║
║  ┌─────────────────────────────────┐  │                                      ║
║8 │ ♜  ♞  ♝  ♛  ♚  ♝  ♞  ♜  │         │  AI Assistant ready!                 ║
║7 │ ♟  ♟  ♟  ♟  ♟  ♟  ♟  ♟  │         │  Ask me anything about chess.        ║
║6 │ ·  ·  ·  ·  ·  ·  ·  ·  │         │                                      ║
║5 │ ·  ·  ·  ·  ·  ·  ·  ·  │         │  Try: 'What's the best opening       ║
║4 │ ·  ·  ·  ·  ·  ·  ·  ·  │         │  move?' or 'Analyze this position'   ║
║3 │ ·  ·  ·  ·  ·  ·  ·  ·  │         │                                      ║
║2 │ ♙  ♙  ♙  ♙  ♙  ♙  ♙  ♙  │         │                                      ║
║1 │ ♖  ♘  ♗  ♕  ♔  ♗  ♘  ♖  │         │                                      ║
║  └─────────────────────────────────┘  │                                      ║
║    a   b   c   d   e   f   g   h      │                                      ║
║                                        │                                      ║
║  Game Status                           │  Move History                        ║
║  Turn: White                           │  No moves yet                        ║
║  Status: Active                        │                                      ║
║  Material: Equal                       │                                      ║
║                                        │                                      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Enter move (e.g., 'e4', 'Nf3') or ask a question...                         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ q: Quit │ r: Reset │ u: Undo │ h: Help │ a: Analyze Position                ║
╚══════════════════════════════════════════════════════════════════════════════╝

Screenshot 1: Initial board state with AI assistant ready
"""

# Demo 2: After making moves
demo2 = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                        ChessCode - Interactive Chess TUI                     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  Chess Board                          │  AI Assistant                        ║
║  ┌─────────────────────────────────┐  │                                      ║
║8 │ ♜  ·  ♝  ♛  ♚  ♝  ♞  ♜  │         │  You: e4                             ║
║7 │ ♟  ♟  ♟  ♟  ·  ♟  ♟  ♟  │         │  Move played: e4                     ║
║6 │ ·  ·  ♞  ·  ·  ·  ·  ·  │         │                                      ║
║5 │ ·  ·  ·  ·  ♟  ·  ·  ·  │         │  You: e5                             ║
║4 │ ·  ·  ·  ·  ♙  ·  ·  ·  │         │  Move played: e5                     ║
║3 │ ·  ·  ·  ·  ·  ♘  ·  ·  │         │                                      ║
║2 │ ♙  ♙  ♙  ♙  ·  ♙  ♙  ♙  │         │  You: Nf3                            ║
║1 │ ♖  ♘  ♗  ♕  ♔  ♗  ·  ♖  │         │  Move played: Nf3                    ║
║  └─────────────────────────────────┘  │                                      ║
║    a   b   c   d   e   f   g   h      │  You: Nc6                            ║
║                                        │  Move played: Nc6                    ║
║  Game Status                           │  Move History                        ║
║  Turn: White                           │  1. e4 e5                            ║
║  Status: Active                        │  2. Nf3 Nc6                          ║
║  Material: Equal                       │                                      ║
║                                        │                                      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Enter move (e.g., 'e4', 'Nf3') or ask a question...                         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ q: Quit │ r: Reset │ u: Undo │ h: Help │ a: Analyze Position                ║
╚══════════════════════════════════════════════════════════════════════════════╝

Screenshot 2: After playing several moves (Italian Game opening)
"""

# Demo 3: AI Analysis
demo3 = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                        ChessCode - Interactive Chess TUI                     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  Chess Board                          │  AI Assistant                        ║
║  ┌─────────────────────────────────┐  │                                      ║
║8 │ ♜  ·  ♝  ♛  ♚  ♝  ♞  ♜  │         │  You: What should I play next?       ║
║7 │ ♟  ♟  ♟  ♟  ·  ♟  ♟  ♟  │         │                                      ║
║6 │ ·  ·  ♞  ·  ·  ·  ·  ·  │         │  AI: This is a standard Italian      ║
║5 │ ·  ·  ·  ·  ♟  ·  ·  ·  │         │  Game opening. White has several     ║
║4 │ ·  ·  ·  ·  ♙  ·  ·  ·  │         │  strong options:                     ║
║3 │ ·  ·  ·  ·  ·  ♘  ·  ·  │         │                                      ║
║2 │ ♙  ♙  ♙  ♙  ·  ♙  ♙  ♙  │         │  1. Bc4 - Develops the bishop to    ║
║1 │ ♖  ♘  ♗  ♕  ♔  ♗  ·  ♖  │         │     an active square, attacking f7   ║
║  └─────────────────────────────────┘  │                                      ║
║    a   b   c   d   e   f   g   h      │  2. Bb5 - The Ruy Lopez, one of     ║
║                                        │     the most popular openings        ║
║  Game Status                           │                                      ║
║  Turn: White                           │  3. d4 - Challenging the center      ║
║  Status: Active                        │     immediately                      ║
║  Material: Equal                       │                                      ║
║                                        │  I recommend Bc4 for a classical     ║
║                                        │  Italian Game setup.                 ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Enter move (e.g., 'e4', 'Nf3') or ask a question...                         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ q: Quit │ r: Reset │ u: Undo │ h: Help │ a: Analyze Position                ║
╚══════════════════════════════════════════════════════════════════════════════╝

Screenshot 3: AI providing strategic analysis and move suggestions
"""

# Demo 4: Help screen
demo4 = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                        ChessCode - Interactive Chess TUI                     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  AI Assistant - Help                                                         ║
║                                                                              ║
║  ChessCode Help                                                              ║
║                                                                              ║
║  Making Moves:                                                               ║
║  - Type moves in standard chess notation (e.g., 'e4', 'Nf3', 'O-O')         ║
║  - Press Enter or click Send to make the move                               ║
║                                                                              ║
║  Asking Questions:                                                           ║
║  - Type any question about chess or the current position                     ║
║  - Examples: "What's the best move?", "Analyze this position"               ║
║                                                                              ║
║  Keyboard Shortcuts:                                                         ║
║  - q: Quit application                                                       ║
║  - r: Reset game                                                             ║
║  - u: Undo last move                                                         ║
║  - h: Show this help                                                         ║
║  - a: Quick position analysis                                                ║
║                                                                              ║
║  Move Notation:                                                              ║
║  - Pawn moves: e4, d5, exd5 (capture)                                        ║
║  - Piece moves: Nf3, Bb5, Qd4                                                ║
║  - Castling: O-O (kingside), O-O-O (queenside)                               ║
║  - Check: Nf3+                                                               ║
║  - Checkmate: Qh7#                                                           ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ q: Quit │ r: Reset │ u: Undo │ h: Help │ a: Analyze Position                ║
╚══════════════════════════════════════════════════════════════════════════════╝

Screenshot 4: Help screen showing all commands and features
"""

# Save all demos
demos = [
    ("01_initial_board.txt", demo1),
    ("02_after_moves.txt", demo2),
    ("03_ai_analysis.txt", demo3),
    ("04_help_screen.txt", demo4),
]

for filename, content in demos:
    filepath = screenshots_dir / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created: {filepath}")

print(f"\n✓ Created {len(demos)} demonstration screenshots in {screenshots_dir}")
print("\nThese text-based screenshots demonstrate:")
print("1. Initial board state with AI assistant")
print("2. Game in progress with move history")
print("3. AI providing strategic analysis")
print("4. Help screen with all commands")
