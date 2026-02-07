#!/usr/bin/env python3
"""Chess TUI - Interactive chess application with a shell-style interface."""
import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

import chess
import chess.svg
from dotenv import load_dotenv

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, Input, Button, Label, RichLog
from textual.reactive import reactive
from textual import on

from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from agents.chess_agent import ChessAgent


# Unicode chess pieces
PIECE_SYMBOLS = {
    'P': '♙', 'N': '♘', 'B': '♗', 'R': '♖', 'Q': '♕', 'K': '♔',
    'p': '♟', 'n': '♞', 'b': '♝', 'r': '♜', 'q': '♛', 'k': '♚',
    '.': '·'
}


class ChessBoard(Static):
    """Widget to display the chess board."""
    
    board = reactive(chess.Board())
    selected_square = reactive(None)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.border_title = "Board"
    
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
    """Widget to display AI chat responses and shell activity."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.border_title = "Terminal"
        self.wrap = True
        self.markup = True


class ChessTUI(App):
    """A Textual TUI for playing chess with a command-driven shell interface."""
    
    CSS = """
    Screen {
        layout: horizontal;
        background: $background;
    }
    
    #shell_container {
        width: 1.8fr;
        height: 100%;
        border: solid $accent;
        padding: 0 1;
    }
    
    #side_container {
        width: 1fr;
        height: 100%;
        border-left: solid $accent;
        padding: 0 1;
    }
    
    ChatLog {
        height: 1fr;
        border: none;
        background: $background;
    }
    
    #input_area {
        height: auto;
        border-top: solid $accent;
        layout: horizontal;
    }
    
    #prompt_label {
        width: auto;
        padding: 1 1;
        color: $accent;
        text-style: bold;
    }
    
    Input {
        width: 1fr;
        border: none;
        background: $background;
    }
    
    ChessBoard {
        height: 20;
        margin-bottom: 1;
        border: solid green;
    }
    
    MoveHistory {
        height: 1fr;
        border: solid yellow;
        margin-bottom: 1;
    }
    
    GameInfo {
        height: 10;
        border: solid blue;
    }
    """
    
    # No global BINDINGS anymore, everything is command-driven
    
    TITLE = "ChessCode Shell"
    
    def __init__(self):
        super().__init__()
        self.board = chess.Board()
        self.agent = None
        self.move_count = 1
        
    async def on_mount(self) -> None:
        """Initialize the application."""
        load_dotenv()
        
        self.chat_log.write(f"[bold cyan]ChessCode CLI - Interactive Chess Agent[/bold cyan]")
        self.chat_log.write(f"[dim]Model: {os.getenv('MODEL', 'grok-4-fast-reasoning')}[/dim]")
        self.chat_log.write(f"[dim]Provider: {os.getenv('MODEL_PROVIDER', 'xai')}[/dim]")
        self.chat_log.write("Type [bold yellow]'help'[/bold yellow] for commands or ask a question.\n")
        
        try:
            self.agent = ChessAgent()
            self.chat_log.write("[bold green]Agent ready![/bold green]")
        except Exception as e:
            self.chat_log.write(f"[bold red]Error initializing agent: {str(e)}[/bold red]")
        
        self.update_game_info()
        self.input.focus()

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        
        with Vertical(id="shell_container"):
            self.chat_log = ChatLog()
            yield self.chat_log
            with Horizontal(id="input_area"):
                yield Label("You: ", id="prompt_label")
                self.input = Input(placeholder="type move or command...")
                yield self.input
        
        with Vertical(id="side_container"):
            self.chess_board = ChessBoard()
            yield self.chess_board
            self.move_history = MoveHistory()
            yield self.move_history
            self.game_info = GameInfo()
            yield self.game_info
            
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

    @on(Input.Submitted)
    async def handle_input(self, event: Input.Submitted) -> None:
        """Handle shell input."""
        user_input = event.value.strip()
        if not user_input:
            return
        
        self.input.value = ""
        self.chat_log.write(f"[bold green]You:[/bold green] {user_input}")
        
        # Command Registry
        cmd = user_input.lower()
        if cmd in ['help', 'h', '?']:
            self.show_help()
        elif cmd in ['reset', 'r', '..']:
            self.reset_game()
        elif cmd in ['undo', 'u']:
            self.undo_move()
        elif cmd in ['analyze', 'a']:
            await self.ask_question("Analyze the current position")
        elif cmd == 'cls':
            self.chat_log.clear()
        elif cmd in ['exit', 'quit', 'q']:
            self.exit()
        else:
            # Not a command, check if it's a move or a generic question
            if self.is_move_notation(user_input):
                await self.make_move(user_input)
            else:
                await self.ask_question(user_input)

    def is_move_notation(self, text: str) -> bool:
        """Check if text looks like a chess move."""
        if len(text) > 10: return False
        move_patterns = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'N', 'B', 'R', 'Q', 'K', 'O-O', '0-0']
        return any(pattern in text for pattern in move_patterns)

    async def make_move(self, move_str: str):
        """Attempt to make a move."""
        try:
            move = self.board.parse_san(move_str)
            if move not in self.board.legal_moves:
                self.chat_log.write(f"[bold red]Illegal move: {move_str}[/bold red]")
                return
            
            san_move = self.board.san(move)
            self.board.push(move)
            self.chess_board.board = self.board
            self.move_history.add_move(san_move, self.move_count)
            
            if not self.board.turn: self.move_count += 1
            self.update_game_info()
            self.chat_log.write(f"[bold green]Move played: {san_move}[/bold green]")
            
            if self.board.is_checkmate():
                self.chat_log.write(f"[bold yellow]Checkmate! {'Black' if self.board.turn else 'White'} wins![/bold yellow]")
        except Exception as e:
            self.chat_log.write(f"[bold red]Invalid move: {move_str}[/bold red]")

    async def ask_question(self, question: str):
        """Query the AI agent."""
        if not self.agent:
            self.chat_log.write("[bold red]Agent not available[/bold red]")
            return
        
        self.chat_log.write("[dim]Thinking...[/dim]")
        try:
            response = await self.agent.query(question, self.board.fen())
            self.chat_log.write(f"[bold cyan]AI:[/bold cyan] {response}")
        except Exception as e:
            self.chat_log.write(f"[bold red]Error: {str(e)}[/bold red]")

    def show_help(self):
        """Show rich help table."""
        table = Table(title="ChessCode Global Commands (BASH-STYLE)", border_style="cyan", show_header=True)
        table.add_column("Command", style="bold yellow")
        table.add_column("Description", style="white")
        table.add_column("Aliases", style="dim white")
        
        table.add_row("help", "Displays this menu", "h, ?")
        table.add_row("<move>", "Make a move (e.g., e4, Nf3)", "-")
        table.add_row("analyze", "Quick position analysis", "a")
        table.add_row("undo", "Undo the last move", "u")
        table.add_row("reset", "Reset the game context", "r, ..")
        table.add_row("cls", "Clear the terminal screen", "-")
        table.add_row("exit", "Quit the application", "q, quit")
        
        self.chat_log.write(table)
        self.chat_log.write("[dim]Note: Any other input is handled by the AI Chess Agent (LangGraph).[/dim]\n")

    def reset_game(self):
        """Reset game state."""
        self.board = chess.Board()
        self.chess_board.board = self.board
        self.move_history.clear_moves()
        self.move_count = 1
        self.update_game_info()
        self.chat_log.write("[bold yellow]Game reset![/bold yellow]")

    def undo_move(self):
        """Undo last move."""
        if len(self.board.move_stack) > 0:
            self.board.pop()
            self.chess_board.board = self.board
            self.update_game_info()
            self.chat_log.write("[bold yellow]Move undone[/bold yellow]")
            # Sync move history - simple refresh by clearing and adding all remaining
            self.move_history.clear_moves()
            temp_board = chess.Board()
            for i, move in enumerate(self.board.move_stack):
                mv_num = (i // 2) + 1
                san = temp_board.san(move)
                self.move_history.add_move(san, mv_num)
                temp_board.push(move)
        else:
            self.chat_log.write("[bold red]No moves to undo[/bold red]")

    def exit(self):
        """Exit the app."""
        self.chat_log.write("[bold red]Exiting...[/bold red]")
        sys.exit(0)


def main():
    app = ChessTUI()
    app.run()


if __name__ == "__main__":
    main()
