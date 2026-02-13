"""PGN file parsing and game search tools."""
import chess.pgn
import io
import os
from pathlib import Path
from typing import List, Dict, Optional


# Encodings to try when reading PGN files
ENCODINGS = ["utf-8", "latin-1", "iso-8859-1", "cp1252"]


def load_pgn_file(filepath: str) -> List[chess.pgn.Game]:
    """Load all games from a PGN file, trying multiple encodings."""
    games = []
    for encoding in ENCODINGS:
        try:
            with open(filepath, "r", encoding=encoding) as f:
                while True:
                    game = chess.pgn.read_game(f)
                    if game is None:
                        break
                    games.append(game)
            return games
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Failed to read {filepath} with any encoding")


def load_all_pgn_files(data_dir: str = "data") -> List[chess.pgn.Game]:
    """Load all PGN games from the data directory."""
    all_games = []
    pgn_dir = Path(data_dir)
    for pgn_path in sorted(pgn_dir.glob("*.pgn")):
        try:
            games = load_pgn_file(str(pgn_path))
            all_games.extend(games)
        except Exception as e:
            print(f"Warning: Failed to load {pgn_path}: {e}")
    return all_games


def game_to_dict(game: chess.pgn.Game) -> Dict:
    """Convert a chess.pgn.Game to a serializable dictionary."""
    headers = dict(game.headers)
    moves_san = []
    board = game.board()
    for move in game.mainline_moves():
        moves_san.append(board.san(move))
        board.push(move)

    return {
        "event": headers.get("Event", ""),
        "site": headers.get("Site", ""),
        "date": headers.get("Date", ""),
        "white": headers.get("White", ""),
        "black": headers.get("Black", ""),
        "result": headers.get("Result", ""),
        "white_elo": headers.get("WhiteElo", ""),
        "black_elo": headers.get("BlackElo", ""),
        "eco": headers.get("ECO", ""),
        "moves_san": " ".join(moves_san),
        "move_count": len(moves_san),
    }


def search_games(
    games: List[chess.pgn.Game] = None,
    player: str = None,
    eco: str = None,
    result: str = None,
    data_dir: str = "data",
) -> List[chess.pgn.Game]:
    """Search games with multiple filter criteria."""
    if games is None:
        games = load_all_pgn_files(data_dir)

    results = []
    for game in games:
        headers = game.headers

        if player:
            player_lower = player.lower()
            white = headers.get("White", "").lower()
            black = headers.get("Black", "").lower()
            if player_lower not in white and player_lower not in black:
                continue

        if eco:
            game_eco = headers.get("ECO", "")
            if not game_eco.upper().startswith(eco.upper()):
                continue

        if result:
            if headers.get("Result", "") != result:
                continue

        results.append(game)

    return results


def find_player_games(
    player_name: str,
    games: List[chess.pgn.Game] = None,
    data_dir: str = "data",
) -> List[chess.pgn.Game]:
    """Find all games where the given player participated."""
    return search_games(games=games, player=player_name, data_dir=data_dir)


def identify_opening(fen: str) -> Optional[Dict]:
    """Identify the opening from a position using ECO-style heuristics.

    Returns a dict with 'eco' and 'name' if recognized, else None.
    """
    # Common opening positions mapped to ECO codes
    KNOWN_POSITIONS = {
        # Starting position
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1": {"eco": "A00", "name": "Starting Position"},
        # 1.e4
        "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1": {"eco": "B00", "name": "King's Pawn Opening"},
        # 1.d4
        "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq - 0 1": {"eco": "D00", "name": "Queen's Pawn Opening"},
        # 1.e4 e5
        "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2": {"eco": "C20", "name": "Open Game"},
        # 1.e4 c5 (Sicilian)
        "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2": {"eco": "B20", "name": "Sicilian Defense"},
        # 1.e4 e6 (French)
        "rnbqkbnr/pppp1ppp/4p3/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2": {"eco": "C00", "name": "French Defense"},
        # 1.e4 c6 (Caro-Kann)
        "rnbqkbnr/pp1ppppp/2p5/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2": {"eco": "B10", "name": "Caro-Kann Defense"},
        # 1.e4 e5 2.Nf3 Nc6 (Two Knights)
        "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3": {"eco": "C40", "name": "King's Knight Opening"},
        # 1.e4 e5 2.Nf3 Nc6 3.Bb5 (Ruy Lopez)
        "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3": {"eco": "C60", "name": "Ruy Lopez"},
        # 1.e4 e5 2.Nf3 Nc6 3.Bc4 (Italian)
        "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3": {"eco": "C50", "name": "Italian Game"},
        # 1.d4 d5 2.c4 (QGD)
        "rnbqkbnr/ppp1pppp/8/3p4/2PP4/8/PP2PPPP/RNBQKBNR b KQkq - 0 2": {"eco": "D06", "name": "Queen's Gambit"},
        # 1.d4 Nf6 2.c4 (Indian)
        "rnbqkb1r/pppppppp/5n2/8/2PP4/8/PP2PPPP/RNBQKBNR b KQkq - 0 2": {"eco": "A45", "name": "Indian Defense"},
        # 1.c4 (English)
        "rnbqkbnr/pppppppp/8/8/2P5/8/PP1PPPPP/RNBQKBNR b KQkq - 0 1": {"eco": "A10", "name": "English Opening"},
        # 1.Nf3 (Reti)
        "rnbqkbnr/pppppppp/8/8/8/5N2/PPPPPPPP/RNBQKB1R b KQkq - 1 1": {"eco": "A04", "name": "Reti Opening"},
    }

    # Normalize FEN (ignore halfmove and fullmove clocks for matching)
    board = chess.Board(fen)
    fen_parts = board.fen().split()
    # Try full match first
    if board.fen() in KNOWN_POSITIONS:
        return KNOWN_POSITIONS[board.fen()]

    # Try matching just the piece placement + turn + castling + en passant
    short_fen = " ".join(fen_parts[:4])
    for known_fen, info in KNOWN_POSITIONS.items():
        known_short = " ".join(known_fen.split()[:4])
        if short_fen == known_short:
            return info

    # Fallback: try to get ECO from game headers if replaying from start
    return None


def get_opening_variations(
    eco: str,
    games: List[chess.pgn.Game] = None,
    data_dir: str = "data",
    max_results: int = 10,
) -> List[Dict]:
    """Get games matching an ECO code as opening variation examples."""
    matching = search_games(games=games, eco=eco, data_dir=data_dir)
    variations = []
    for game in matching[:max_results]:
        board = game.board()
        moves = []
        for i, move in enumerate(game.mainline_moves()):
            if i >= 20:  # Only first 20 moves (opening phase)
                break
            moves.append(board.san(move))
            board.push(move)
        variations.append({
            "white": game.headers.get("White", ""),
            "black": game.headers.get("Black", ""),
            "eco": game.headers.get("ECO", ""),
            "result": game.headers.get("Result", ""),
            "moves": " ".join(
                f"{i // 2 + 1}.{'' if i % 2 == 0 else '..'}{m}"
                for i, m in enumerate(moves)
            ),
        })
    return variations


def parse_pgn_string(pgn_text: str) -> Optional[chess.pgn.Game]:
    """Parse a single PGN string into a Game object."""
    return chess.pgn.read_game(io.StringIO(pgn_text))
