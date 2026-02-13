"""Board analysis tools - pure python-chess position evaluation."""
import chess
from typing import Dict, List, Optional


# Standard piece values
PIECE_VALUES = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
}


def count_material(board: chess.Board) -> Dict[str, int]:
    """Count material for both sides."""
    white = sum(
        len(board.pieces(pt, chess.WHITE)) * val
        for pt, val in PIECE_VALUES.items()
    )
    black = sum(
        len(board.pieces(pt, chess.BLACK)) * val
        for pt, val in PIECE_VALUES.items()
    )
    return {"white": white, "black": black}


def analyze_position(fen: str = None) -> str:
    """Analyze a chess position given its FEN string.

    Returns a human-readable analysis including material balance,
    check/mate status, and legal move count.
    """
    try:
        board = chess.Board(fen) if fen else chess.Board()
        material = count_material(board)

        in_check = board.is_check()
        checkmate = board.is_checkmate()
        stalemate = board.is_stalemate()
        legal_moves = board.legal_moves.count()

        diff = material["white"] - material["black"]
        if diff > 0:
            advantage = f"White +{diff}"
        elif diff < 0:
            advantage = f"Black +{abs(diff)}"
        else:
            advantage = "Equal"

        analysis = (
            f"Position Analysis:\n"
            f"- Turn: {'White' if board.turn else 'Black'}\n"
            f"- Material: White {material['white']}, Black {material['black']} ({advantage})\n"
            f"- Check: {'Yes' if in_check else 'No'}\n"
            f"- Checkmate: {'Yes' if checkmate else 'No'}\n"
            f"- Stalemate: {'Yes' if stalemate else 'No'}\n"
            f"- Legal moves available: {legal_moves}\n"
            f"- FEN: {board.fen()}"
        )
        return analysis
    except Exception as e:
        return f"Error analyzing position: {e}"


def suggest_move(fen: str = None) -> str:
    """Suggest a move using simple heuristics (captures > center > development)."""
    try:
        board = chess.Board(fen) if fen else chess.Board()

        if board.is_game_over():
            return "Game is over. No moves available."

        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return "No legal moves available."

        captures = [m for m in legal_moves if board.is_capture(m)]
        center_squares = [chess.E4, chess.D4, chess.E5, chess.D5]
        center_moves = [m for m in legal_moves if m.to_square in center_squares]

        if captures:
            suggested = captures[0]
            reason = "Capturing opponent's piece"
        elif center_moves:
            suggested = center_moves[0]
            reason = "Controlling the center"
        else:
            suggested = legal_moves[0]
            reason = "Developing pieces"

        return f"Suggested move: {board.san(suggested)} - {reason}"
    except Exception as e:
        return f"Error suggesting move: {e}"


def explain_move(move_san: str, fen: str = None) -> str:
    """Explain a specific chess move."""
    try:
        board = chess.Board(fen) if fen else chess.Board()

        try:
            parsed_move = board.parse_san(move_san)
        except ValueError:
            return f"Invalid move notation: {move_san}"

        if parsed_move not in board.legal_moves:
            return f"Illegal move: {move_san}"

        is_capture = board.is_capture(parsed_move)
        gives_check = board.gives_check(parsed_move)

        explanation = f"Move {move_san}:\n"
        explanation += f"- From: {chess.square_name(parsed_move.from_square)}\n"
        explanation += f"- To: {chess.square_name(parsed_move.to_square)}\n"

        if is_capture:
            explanation += "- This is a capture\n"
        if gives_check:
            explanation += "- This move gives check\n"

        return explanation
    except Exception as e:
        return f"Error explaining move: {e}"


def get_game_phase(fen: str) -> str:
    """Determine game phase based on piece count and move number.

    Returns 'opening', 'middlegame', or 'endgame'.
    """
    board = chess.Board(fen)
    minor_and_major = sum(
        len(board.pieces(pt, color))
        for pt in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]
        for color in [chess.WHITE, chess.BLACK]
    )
    if board.fullmove_number <= 15 and minor_and_major >= 12:
        return "opening"
    elif minor_and_major <= 6:
        return "endgame"
    return "middlegame"


def get_legal_moves(fen: str) -> List[str]:
    """Return all legal moves in SAN notation."""
    board = chess.Board(fen)
    return [board.san(m) for m in board.legal_moves]
