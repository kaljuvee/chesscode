#!/usr/bin/env python3
"""Chess TUI - Interactive chess application with AI assistance."""
import asyncio
import os
from pathlib import Path
from datetime import datetime

import chess
import chess.svg
from dotenv import load_dotenv

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, Input, Button, Label, RichLog
from textual.binding import Binding
from textual.reactive import reactive

from agents.chess_agent import ChessAgent


# Unicode chess pieces
PIECE_SYMBOLS = {
    'P': '♙', 'N': '♘', 'B': '♗', 'R': '♖', 'Q': '♕', 'K': '♔',
    'p': '♟', 'n': '♞', 'b': '♝', 'r': '♜', 'q': '♛', 'k': '♚',
    '.': '·'
}

PIECE_COLORS = {
    'P': 'bold white', 'N': 'bold white', 'B': 'bold white', 
    'R': 'bold white', 'Q': 'bold white', 'K': 'bold white',
    'p': 'bold black', 'n': 'bold black', 'b': 'bold black',
    'r': 'bold black', 'q': 'bold black', 'k': 'bold black',
    '.': 'dim white'
}


class ChessBoard(Static):
    """Widget to display the chess board."""
    
    board = reactive(chess.Board())
    selected_square = reactive(None)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.border_title = "Chess Board"
    
    def render(self) -> str:
        """Render the chess board with Unicode pieces."""
        lines = []
        lines.append("  ┌─────────────────────────────────┐")
        
        for rank in range(7, -1, -1):
            rank_str = f"{rank + 1} │ "
            for file in range(8):
                square = chess.square(file, rank)
                piece = self.board.piece_at(square)
                
                if piece:
                    symbol = PIECE_SYMBOLS.get(piece.symbol(), '?')
                else:
                    symbol = PIECE_SYMBOLS['.']
                
                # Highlight selected square
                if self.selected_square == square:
                    rank_str += f"[reverse]{symbol}[/reverse]  "
                else:
                    # Alternate square colors
                    if (rank + file) % 2 == 0:
                        rank_str += f"[dim]{symbol}[/dim]  "
                    else:
                        rank_str += f"{symbol}  "
            
            rank_str += "│"
            lines.append(rank_str)
        
        lines.append("  └─────────────────────────────────┘")
        lines.append("    a   b   c   d   e   f   g   h")
        
        return "\n".join(lines)
    
    def watch_board(self, board: chess.Board) -> None:
        """React to board changes."""
        self.refresh()
    
    def watch_selected_square(self, square: int) -> None:
        """React to square selection changes."""
        self.refresh()


class MoveHistory(ScrollableContainer):
    """Widget to display move history."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.border_title = "Move History"
        self.moves = []
    
    def add_move(self, move: str, move_number: int):
        """Add a move to the history."""
        self.moves.append((move_number, move))
        self.refresh_display()
    
    def clear_moves(self):
        """Clear all moves."""
        self.moves = []
        self.refresh_display()
    
    def refresh_display(self):
        """Refresh the move display."""
        self.remove_children()
        
        if not self.moves:
            self.mount(Label("No moves yet"))
            return
        
        for i in range(0, len(self.moves), 2):
            move_num = self.moves[i][0]
            white_move = self.moves[i][1]
            black_move = self.moves[i + 1][1] if i + 1 < len(self.moves) else "..."
            
            move_text = f"{move_num}. {white_move} {black_move}"
            self.mount(Label(move_text))


class GameInfo(Static):
    """Widget to display game information."""
    
    turn = reactive("White")
    status = reactive("Active")
    material = reactive("Equal")
    
    def render(self) -> str:
        """Render game information."""
        return f"""[bold]Game Status[/bold]
Turn: {self.turn}
Status: {self.status}
Material: {self.material}"""


class ChatLog(RichLog):
    """Widget to display AI chat responses."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.border_title = "AI Assistant"


class ChessTUI(App):
    """A Textual TUI for playing chess with AI assistance."""
    
    CSS = """
    Screen {
        layout: grid;
        grid-size: 3 3;
        grid-rows: auto 1fr auto;
    }
    
    Header {
        column-span: 3;
    }
    
    Footer {
        column-span: 3;
    }
    
    #board_container {
        row-span: 2;
        width: 45;
    }
    
    #info_container {
        row-span: 1;
    }
    
    #history_container {
        row-span: 1;
    }
    
    #chat_container {
        column-span: 2;
        row-span: 2;
    }
    
    ChessBoard {
        height: 20;
        border: solid green;
    }
    
    GameInfo {
        height: 10;
        border: solid blue;
    }
    
    MoveHistory {
        height: 10;
        border: solid yellow;
    }
    
    ChatLog {
        border: solid cyan;
    }
    
    #input_container {
        column-span: 3;
        height: auto;
        layout: horizontal;
    }
    
    Input {
        width: 1fr;
    }
    
    Button {
        width: auto;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "reset", "Reset Game"),
        Binding("u", "undo", "Undo Move"),
        Binding("h", "help", "Help"),
        Binding("a", "analyze", "Analyze Position"),
    ]
    
    TITLE = "ChessCode - Interactive Chess TUI"
    
    def __init__(self):
        super().__init__()
        self.board = chess.Board()
        self.agent = None
        self.move_count = 1
        self.selected_square = None
    
    async def on_mount(self) -> None:
        """Initialize the application."""
        # Load environment variables
        load_dotenv()
        
        # Initialize chess agent
        self.chat_log.write("[bold green]Initializing AI Chess Assistant...[/bold green]")
        try:
            self.agent = ChessAgent()
            self.chat_log.write("[bold green]AI Assistant ready! Ask me anything about chess.[/bold green]")
            self.chat_log.write("[dim]Try: 'What's the best opening move?' or 'Analyze this position'[/dim]")
        except Exception as e:
            self.chat_log.write(f"[bold red]Error initializing AI: {str(e)}[/bold red]")
        
        self.update_game_info()
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        
        # Left column - Board and info
        with Vertical(id="board_container"):
            self.chess_board = ChessBoard()
            yield self.chess_board
        
        with Vertical(id="info_container"):
            self.game_info = GameInfo()
            yield self.game_info
        
        with Vertical(id="history_container"):
            self.move_history = MoveHistory()
            yield self.move_history
        
        # Right column - Chat
        with Vertical(id="chat_container"):
            self.chat_log = ChatLog()
            yield self.chat_log
        
        # Bottom - Input
        with Horizontal(id="input_container"):
            self.input = Input(placeholder="Enter move (e.g., 'e4', 'Nf3') or ask a question...")
            yield self.input
            yield Button("Send", id="send_btn", variant="primary")
        
        yield Footer()
    
    def update_game_info(self):
        """Update game information display."""
        self.game_info.turn = "White" if self.board.turn else "Black"
        
        if self.board.is_checkmate():
            self.game_info.status = "Checkmate!"
        elif self.board.is_stalemate():
            self.game_info.status = "Stalemate"
        elif self.board.is_check():
            self.game_info.status = "Check!"
        else:
            self.game_info.status = "Active"
        
        # Calculate material
        material = {
            "white": sum([len(self.board.pieces(pt, chess.WHITE)) * [0, 1, 3, 3, 5, 9][pt] 
                         for pt in range(1, 6)]),
            "black": sum([len(self.board.pieces(pt, chess.BLACK)) * [0, 1, 3, 3, 5, 9][pt] 
                         for pt in range(1, 6)])
        }
        
        diff = material['white'] - material['black']
        if diff > 0:
            self.game_info.material = f"White +{diff}"
        elif diff < 0:
            self.game_info.material = f"Black +{abs(diff)}"
        else:
            self.game_info.material = "Equal"
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "send_btn":
            await self.process_input()
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        await self.process_input()
    
    async def process_input(self):
        """Process user input (move or question)."""
        user_input = self.input.value.strip()
        if not user_input:
            return
        
        self.input.value = ""
        
        # Check if it's a move or a question
        if self.is_move_notation(user_input):
            await self.make_move(user_input)
        else:
            await self.ask_question(user_input)
    
    def is_move_notation(self, text: str) -> bool:
        """Check if text looks like a chess move."""
        # Simple heuristic: short strings with chess notation patterns
        if len(text) > 10:
            return False
        
        # Common move patterns
        move_patterns = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h',  # pawn moves
                        'N', 'B', 'R', 'Q', 'K',  # piece moves
                        'O-O', '0-0',  # castling
                        'x', '+', '#']  # captures, check, checkmate
        
        return any(pattern in text for pattern in move_patterns)
    
    async def make_move(self, move_str: str):
        """Attempt to make a move on the board."""
        try:
            # Try to parse the move
            move = self.board.parse_san(move_str)
            
            if move not in self.board.legal_moves:
                self.chat_log.write(f"[bold red]Illegal move: {move_str}[/bold red]")
                return
            
            # Make the move
            san_move = self.board.san(move)
            self.board.push(move)
            
            # Update display
            self.chess_board.board = self.board
            self.move_history.add_move(san_move, self.move_count)
            
            if not self.board.turn:  # If it's now black's turn, increment move count
                self.move_count += 1
            
            self.update_game_info()
            
            self.chat_log.write(f"[bold green]Move played: {san_move}[/bold green]")
            
            # Check game status
            if self.board.is_checkmate():
                winner = "Black" if self.board.turn else "White"
                self.chat_log.write(f"[bold yellow]Checkmate! {winner} wins![/bold yellow]")
            elif self.board.is_stalemate():
                self.chat_log.write("[bold yellow]Stalemate! Game is a draw.[/bold yellow]")
            elif self.board.is_check():
                self.chat_log.write("[bold yellow]Check![/bold yellow]")
        
        except ValueError as e:
            self.chat_log.write(f"[bold red]Invalid move: {move_str}[/bold red]")
        except Exception as e:
            self.chat_log.write(f"[bold red]Error: {str(e)}[/bold red]")
    
    async def ask_question(self, question: str):
        """Ask the AI assistant a question."""
        if not self.agent:
            self.chat_log.write("[bold red]AI Assistant not available[/bold red]")
            return
        
        self.chat_log.write(f"[bold cyan]You:[/bold cyan] {question}")
        self.chat_log.write("[dim]Thinking...[/dim]")
        
        try:
            response = await self.agent.query(question, self.board.fen())
            self.chat_log.write(f"[bold green]AI:[/bold green] {response}")
        except Exception as e:
            self.chat_log.write(f"[bold red]Error: {str(e)}[/bold red]")
    
    def action_reset(self) -> None:
        """Reset the game."""
        self.board = chess.Board()
        self.chess_board.board = self.board
        self.move_history.clear_moves()
        self.move_count = 1
        self.update_game_info()
        self.chat_log.write("[bold yellow]Game reset![/bold yellow]")
    
    def action_undo(self) -> None:
        """Undo the last move."""
        if len(self.board.move_stack) > 0:
            self.board.pop()
            self.chess_board.board = self.board
            self.update_game_info()
            self.chat_log.write("[bold yellow]Move undone[/bold yellow]")
            # Rebuild move history
            self.move_history.clear_moves()
            move_num = 1
            for i, move in enumerate(self.board.move_stack):
                if i % 2 == 0:
                    self.move_history.add_move(self.board.san(move), move_num)
                else:
                    self.move_history.add_move(self.board.san(move), move_num)
                    move_num += 1
        else:
            self.chat_log.write("[bold red]No moves to undo[/bold red]")
    
    def action_help(self) -> None:
        """Show help information."""
        help_text = """[bold]ChessCode Help[/bold]

[bold cyan]Making Moves:[/bold cyan]
- Type moves in standard chess notation (e.g., 'e4', 'Nf3', 'O-O')
- Press Enter or click Send to make the move

[bold cyan]Asking Questions:[/bold cyan]
- Type any question about chess or the current position
- Examples: "What's the best move?", "Analyze this position", "Explain this opening"

[bold cyan]Keyboard Shortcuts:[/bold cyan]
- q: Quit application
- r: Reset game
- u: Undo last move
- h: Show this help
- a: Quick position analysis

[bold cyan]Move Notation:[/bold cyan]
- Pawn moves: e4, d5, exd5 (capture)
- Piece moves: Nf3, Bb5, Qd4
- Castling: O-O (kingside), O-O-O (queenside)
- Check: Nf3+
- Checkmate: Qh7#"""
        
        self.chat_log.write(help_text)
    
    async def action_analyze(self) -> None:
        """Quick position analysis."""
        await self.ask_question("Analyze the current position")


def main():
    """Run the Chess TUI application."""
    app = ChessTUI()
    app.run()


if __name__ == "__main__":
    main()
