#!/usr/bin/env python3
"""Chess TUI - Interactive chess application with multi-agent AI system."""
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


# Unicode chess pieces
PIECE_SYMBOLS = {
    'P': '\u2659', 'N': '\u2658', 'B': '\u2657', 'R': '\u2656', 'Q': '\u2655', 'K': '\u2654',
    'p': '\u265f', 'n': '\u265e', 'b': '\u265d', 'r': '\u265c', 'q': '\u265b', 'k': '\u265a',
    '.': '\u00b7'
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
        lines.append("  \u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510")

        for rank in range(7, -1, -1):
            rank_str = f"{rank + 1} \u2502 "
            for file in range(8):
                square = chess.square(file, rank)
                piece = self.board.piece_at(square)

                if piece:
                    symbol = PIECE_SYMBOLS.get(piece.symbol(), '?')
                else:
                    symbol = PIECE_SYMBOLS['.']

                if self.selected_square == square:
                    rank_str += f"[reverse]{symbol}[/reverse]  "
                else:
                    if (rank + file) % 2 == 0:
                        rank_str += f"[dim]{symbol}[/dim]  "
                    else:
                        rank_str += f"{symbol}  "

            rank_str += "\u2502"
            lines.append(rank_str)

        lines.append("  \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518")
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
        self.moves.append((move_number, move))
        self.refresh_display()

    def clear_moves(self):
        self.moves = []
        self.refresh_display()

    def refresh_display(self):
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
    """Widget to display game information and active agent."""

    turn = reactive("White")
    status = reactive("Active")
    material = reactive("Equal")
    active_agent = reactive("Auto (Router)")

    def render(self) -> str:
        return (
            f"[bold]Game Status[/bold]\n"
            f"Turn: {self.turn}\n"
            f"Status: {self.status}\n"
            f"Material: {self.material}\n"
            f"Agent: {self.active_agent}"
        )


class ChatLog(RichLog):
    """Widget to display AI chat responses and shell activity."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.border_title = "Terminal"
        self.wrap = True
        self.markup = True


# Agent name aliases for user convenience
AGENT_ALIASES = {
    "general": "general",
    "gen": "general",
    "db": "general",
    "coach": "children_coach",
    "child": "children_coach",
    "kids": "children_coach",
    "opening": "opening_teacher",
    "openings": "opening_teacher",
    "variation": "opening_teacher",
    "analyst": "player_analyst",
    "analyze_player": "player_analyst",
    "spy": "player_analyst",
    "pgn-spy": "player_analyst",
    "teacher": "personal_teacher",
    "personal": "personal_teacher",
    "improve": "personal_teacher",
    "engine": "engine",
    "stockfish": "engine",
    "sf": "engine",
    "auto": None,  # Reset to auto-routing
}


class ChessTUI(App):
    """A Textual TUI for playing chess with a multi-agent AI system."""

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
        height: 12;
        border: solid blue;
    }
    """

    TITLE = "ChessCode Shell"

    def __init__(self):
        super().__init__()
        self.board = chess.Board()
        self.router = None
        self.move_count = 1

    async def on_mount(self) -> None:
        """Initialize the application and all agents."""
        load_dotenv()

        self.chat_log.write("[bold cyan]ChessCode CLI - Multi-Agent Chess System[/bold cyan]")
        self.chat_log.write(f"[dim]Model: {os.getenv('MODEL', 'grok-4-fast-reasoning')}[/dim]")
        self.chat_log.write(f"[dim]Provider: {os.getenv('MODEL_PROVIDER', 'xai')}[/dim]")
        self.chat_log.write("Type [bold yellow]'help'[/bold yellow] for commands or ask a question.\n")

        try:
            from agents.router import Router
            from agents.general_agent import GeneralAgent
            from agents.engine_agent import EngineAgent
            from agents.children_coach import ChildrenCoachAgent
            from agents.opening_teacher import OpeningTeacherAgent
            from agents.player_analyst import PlayerAnalystAgent
            from agents.personal_teacher import PersonalTeacherAgent

            agents = {
                "general": GeneralAgent(),
                "engine": EngineAgent(),
                "children_coach": ChildrenCoachAgent(),
                "opening_teacher": OpeningTeacherAgent(),
                "player_analyst": PlayerAnalystAgent(),
                "personal_teacher": PersonalTeacherAgent(),
            }
            self.router = Router(agents)

            agent_names = ", ".join(agents.keys())
            self.chat_log.write(f"[bold green]Agent system ready![/bold green]")
            self.chat_log.write(f"[dim]Agents: {agent_names}[/dim]")
        except Exception as e:
            self.chat_log.write(f"[bold red]Error initializing agents: {str(e)}[/bold red]")
            self.chat_log.write("[dim]Falling back to basic mode.[/dim]")

        self.update_game_info()
        self.input.focus()

    def compose(self) -> ComposeResult:
        yield Header()

        with Vertical(id="shell_container"):
            self.chat_log = ChatLog()
            yield self.chat_log
            with Horizontal(id="input_area"):
                yield Label("You: ", id="prompt_label")
                self.input = Input(placeholder="type move, command, or question...")
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
        """Handle shell input - commands, moves, and AI queries."""
        user_input = event.value.strip()
        if not user_input:
            return

        self.input.value = ""
        self.chat_log.write(f"[bold green]You:[/bold green] {user_input}")

        cmd = user_input.lower()

        # Command Registry
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
            self.exit_app()
        elif cmd == 'agents':
            self.show_agents()
        elif cmd.startswith('agent '):
            agent_name = cmd.split(' ', 1)[1].strip()
            self.set_agent(agent_name)
        elif cmd.startswith('label '):
            await self.handle_label_command(user_input[6:].strip())
        elif cmd.startswith('import '):
            filepath = user_input[7:].strip()
            await self.import_pgn(filepath)
        else:
            if self.is_move_notation(user_input):
                await self.make_move(user_input)
            else:
                await self.ask_question(user_input)

    def is_move_notation(self, text: str) -> bool:
        """Check if text looks like a chess move."""
        if len(text) > 10:
            return False
        move_patterns = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h',
                         'N', 'B', 'R', 'Q', 'K', 'O-O', '0-0']
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

            if not self.board.turn:
                self.move_count += 1
            self.update_game_info()
            self.chat_log.write(f"[bold green]Move played: {san_move}[/bold green]")

            if self.board.is_checkmate():
                winner = 'Black' if self.board.turn else 'White'
                self.chat_log.write(
                    f"[bold yellow]Checkmate! {winner} wins![/bold yellow]"
                )
        except Exception:
            self.chat_log.write(f"[bold red]Invalid move: {move_str}[/bold red]")

    async def ask_question(self, question: str):
        """Query the AI agent system via the router."""
        if not self.router:
            self.chat_log.write("[bold red]Agent system not available[/bold red]")
            return

        self.chat_log.write("[dim]Thinking...[/dim]")
        try:
            move_history = [str(m) for m in self.board.move_stack]
            response = await self.router.query(
                question, self.board.fen(), move_history
            )
            agent_name = self.router.last_agent_name
            self.chat_log.write(f"[dim][{agent_name}][/dim]")
            self.chat_log.write(f"[bold cyan]AI:[/bold cyan] {response}")
            self.game_info.active_agent = agent_name
        except Exception as e:
            self.chat_log.write(f"[bold red]Error: {str(e)}[/bold red]")

    def show_help(self):
        """Show rich help table with all commands."""
        table = Table(
            title="ChessCode Commands", border_style="cyan", show_header=True
        )
        table.add_column("Command", style="bold yellow")
        table.add_column("Description", style="white")
        table.add_column("Aliases", style="dim white")

        table.add_row("help", "Display this menu", "h, ?")
        table.add_row("<move>", "Make a move (e.g., e4, Nf3, O-O)", "-")
        table.add_row("analyze", "Quick position analysis", "a")
        table.add_row("undo", "Undo the last move", "u")
        table.add_row("reset", "Reset the game", "r, ..")
        table.add_row("agents", "List all available agents", "-")
        table.add_row(
            "agent <name>",
            "Force a specific agent (or 'auto' to reset)",
            "-",
        )
        table.add_row("label <args>", "Add label/mask to current position", "-")
        table.add_row("import <file>", "Import a PGN file", "-")
        table.add_row("cls", "Clear the terminal screen", "-")
        table.add_row("exit", "Quit the application", "q, quit")

        self.chat_log.write(table)

        agent_table = Table(
            title="Agent Aliases", border_style="green", show_header=True
        )
        agent_table.add_column("Agent", style="bold green")
        agent_table.add_column("Aliases", style="white")
        agent_table.add_column("Purpose", style="dim white")

        agent_table.add_row("general", "gen, db", "Database search & general Q&A")
        agent_table.add_row("engine", "stockfish, sf", "Position evaluation & best moves")
        agent_table.add_row("children_coach", "coach, child, kids", "Beginner/children teaching")
        agent_table.add_row("opening_teacher", "opening, variation", "Opening theory & variations")
        agent_table.add_row("player_analyst", "analyst, spy, pgn-spy", "PGN-Spy style statistics")
        agent_table.add_row("personal_teacher", "teacher, personal", "Personalized coaching")
        agent_table.add_row("auto", "-", "Reset to automatic routing")

        self.chat_log.write(agent_table)
        self.chat_log.write(
            "[dim]Any other input is routed to the best agent automatically.[/dim]\n"
        )

    def show_agents(self):
        """List all available agents and their status."""
        if not self.router:
            self.chat_log.write("[bold red]Agent system not initialized[/bold red]")
            return

        table = Table(
            title="Available Agents", border_style="green", show_header=True
        )
        table.add_column("Name", style="bold green")
        table.add_column("Status", style="white")

        for name in self.router.agents:
            status = "[bold green]Ready[/bold green]"
            if name == self.router.last_agent_name:
                status += " [dim](last used)[/dim]"
            table.add_row(name, status)

        self.chat_log.write(table)

        forced = self.router._forced_agent
        if forced:
            self.chat_log.write(
                f"[dim]Forced agent: {forced} (will be used for next query)[/dim]"
            )
        else:
            self.chat_log.write("[dim]Routing: automatic (LLM classifier)[/dim]")

    def set_agent(self, alias: str):
        """Set the active agent by name or alias."""
        if not self.router:
            self.chat_log.write("[bold red]Agent system not initialized[/bold red]")
            return

        resolved = AGENT_ALIASES.get(alias, alias)

        if resolved is None:
            # Reset to auto
            self.router.clear_forced_agent()
            self.game_info.active_agent = "Auto (Router)"
            self.chat_log.write("[bold yellow]Agent reset to automatic routing[/bold yellow]")
        elif self.router.force_agent(resolved):
            self.game_info.active_agent = resolved
            self.chat_log.write(
                f"[bold green]Agent set to: {resolved}[/bold green] "
                f"[dim](will be used for next query only)[/dim]"
            )
        else:
            available = ", ".join(list(self.router.agents.keys()) + ["auto"])
            self.chat_log.write(
                f"[bold red]Unknown agent: {alias}[/bold red]\n"
                f"[dim]Available: {available}[/dim]"
            )

    async def handle_label_command(self, args: str):
        """Handle the label command for adding PGN labels/masks.

        Usage:
            label <type> <value>        - Label the current position
            label nag $1                - Add NAG annotation (good move)
            label comment "text"        - Add a comment
            label theme pin             - Tag with tactical theme
            label opening "Sicilian"    - Tag opening name
        """
        parts = args.split(None, 1)
        if len(parts) < 2:
            self.chat_log.write(
                "[bold yellow]Usage: label <type> <value>[/bold yellow]\n"
                "[dim]Types: nag, comment, theme, opening, tactic, endgame, mask, custom[/dim]\n"
                "[dim]Example: label theme pin[/dim]\n"
                "[dim]Example: label comment \"Interesting position\"[/dim]"
            )
            return

        label_type = parts[0].strip()
        label_value = parts[1].strip().strip('"').strip("'")
        fen = self.board.fen()
        move_num = len(self.board.move_stack)

        valid_types = {
            "nag", "comment", "theme", "opening", "tactic",
            "endgame", "mask", "custom",
        }
        if label_type not in valid_types:
            self.chat_log.write(
                f"[bold red]Invalid label type: {label_type}[/bold red]\n"
                f"[dim]Valid types: {', '.join(sorted(valid_types))}[/dim]"
            )
            return

        # Try database storage first
        try:
            from tools.db_tools import add_label
            label_id = await add_label(
                game_id=0,  # Current game (not yet in DB)
                label_type=label_type,
                label_value=label_value,
                position_fen=fen,
                move_number=move_num,
            )
            if label_id:
                self.chat_log.write(
                    f"[bold green]Label added (DB #{label_id}): "
                    f"{label_type}={label_value}[/bold green]"
                )
                return
        except Exception:
            pass

        # Fallback: store in memory / display confirmation
        self.chat_log.write(
            f"[bold green]Label: {label_type}={label_value}[/bold green]\n"
            f"[dim]Position: {fen}[/dim]\n"
            f"[dim]Move: {move_num}[/dim]\n"
            f"[dim](Database not connected - label stored in session)[/dim]"
        )

    async def import_pgn(self, filepath: str):
        """Import a PGN file for analysis."""
        path = Path(filepath)
        if not path.exists():
            # Try relative to data/ directory
            path = Path("data") / filepath
            if not path.exists():
                self.chat_log.write(f"[bold red]File not found: {filepath}[/bold red]")
                return

        self.chat_log.write(f"[dim]Loading {path.name}...[/dim]")
        try:
            from tools.pgn_tools import load_pgn_file
            games = load_pgn_file(str(path))
            self.chat_log.write(
                f"[bold green]Loaded {len(games)} games from {path.name}[/bold green]"
            )
        except Exception as e:
            self.chat_log.write(f"[bold red]Error loading PGN: {e}[/bold red]")

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
            self.move_history.clear_moves()
            temp_board = chess.Board()
            for i, move in enumerate(self.board.move_stack):
                mv_num = (i // 2) + 1
                san = temp_board.san(move)
                self.move_history.add_move(san, mv_num)
                temp_board.push(move)
        else:
            self.chat_log.write("[bold red]No moves to undo[/bold red]")

    def exit_app(self):
        """Exit the app."""
        self.chat_log.write("[bold red]Exiting...[/bold red]")
        sys.exit(0)


def main():
    app = ChessTUI()
    app.run()


if __name__ == "__main__":
    main()
