"""Stockfish engine integration tools.

Provides async wrappers around the python stockfish package.
The engine binary must be installed separately (e.g. apt install stockfish).
"""
import asyncio
import os
from typing import Dict, List, Optional

import chess
import chess.pgn
import io

from .board_tools import get_game_phase

# Lazy import - stockfish may not be installed
_engine = None


def _get_engine():
    """Get or create the singleton Stockfish instance."""
    global _engine
    if _engine is None:
        try:
            from stockfish import Stockfish
        except ImportError:
            raise RuntimeError(
                "stockfish package not installed. Run: pip install stockfish"
            )
        path = os.getenv("STOCKFISH_PATH", "/usr/games/stockfish")
        if not os.path.exists(path):
            raise RuntimeError(
                f"Stockfish binary not found at {path}. "
                "Install it (apt install stockfish) or set STOCKFISH_PATH."
            )
        _engine = Stockfish(
            path=path,
            depth=20,
            parameters={"Threads": 2, "Hash": 256},
        )
    return _engine


async def analyze_position(
    fen: str, depth: int = 20, num_lines: int = 3
) -> Dict:
    """Analyze a position and return evaluation + top lines.

    Runs Stockfish in a thread executor to avoid blocking the async event loop.
    """
    def _analyze():
        engine = _get_engine()
        engine.set_fen_position(fen)
        engine.set_depth(depth)
        evaluation = engine.get_evaluation()
        top_moves = engine.get_top_moves(num_lines)
        return {
            "evaluation": evaluation,
            "lines": top_moves,
            "fen": fen,
            "depth": depth,
        }

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _analyze)


async def get_best_move(fen: str, time_ms: int = 1000) -> str:
    """Get the engine's best move for a position."""
    def _best():
        engine = _get_engine()
        engine.set_fen_position(fen)
        return engine.get_best_move_time(time_ms)

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _best)


async def evaluate_move(fen: str, move_uci: str, depth: int = 18) -> Dict:
    """Evaluate a specific move by comparing before/after position scores."""
    def _eval():
        engine = _get_engine()
        # Eval before
        engine.set_fen_position(fen)
        engine.set_depth(depth)
        eval_before = engine.get_evaluation()
        best_move = engine.get_best_move()

        # Make the move and eval after
        board = chess.Board(fen)
        move = chess.Move.from_uci(move_uci)
        board.push(move)
        engine.set_fen_position(board.fen())
        engine.set_depth(depth)
        eval_after = engine.get_evaluation()

        return {
            "eval_before": eval_before,
            "eval_after": eval_after,
            "best_move": best_move,
            "played_move": move_uci,
            "is_best": move_uci == best_move,
        }

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _eval)


def _cp_value(evaluation: Dict) -> float:
    """Convert Stockfish evaluation dict to centipawn value."""
    if evaluation["type"] == "cp":
        return evaluation["value"]
    elif evaluation["type"] == "mate":
        # Assign a large value for mate scores
        return 10000 if evaluation["value"] > 0 else -10000
    return 0


async def batch_analyze_games(
    games: List[chess.pgn.Game],
    depth: int = 18,
    skip_opening_moves: int = 0,
) -> Dict:
    """Analyze all moves in multiple games. Returns PGN-Spy style statistics.

    Calculates:
    - ACPL (Average CentiPawn Loss)
    - Blunder/mistake/inaccuracy rates
    - T1/T2/T3 accuracy (top engine move matches)
    - Phase breakdown (opening/middlegame/endgame)
    """
    def _batch():
        engine = _get_engine()
        stats = {
            "total_positions": 0,
            "total_cpl": 0.0,
            "blunders": 0,       # >200cp loss
            "mistakes": 0,       # 100-200cp loss
            "inaccuracies": 0,   # 50-100cp loss
            "t1_matches": 0,     # matched engine's #1 choice
            "t2_matches": 0,     # matched top-2
            "t3_matches": 0,     # matched top-3
            "phase_stats": {
                "opening": {"positions": 0, "total_cpl": 0.0, "blunders": 0},
                "middlegame": {"positions": 0, "total_cpl": 0.0, "blunders": 0},
                "endgame": {"positions": 0, "total_cpl": 0.0, "blunders": 0},
            },
            "games_analyzed": 0,
        }

        for game in games:
            board = game.board()
            move_num = 0

            for move in game.mainline_moves():
                move_num += 1
                if move_num <= skip_opening_moves:
                    board.push(move)
                    continue

                fen = board.fen()
                phase = get_game_phase(fen)

                try:
                    engine.set_fen_position(fen)
                    engine.set_depth(depth)
                    eval_before = engine.get_evaluation()
                    top_moves = engine.get_top_moves(3)
                    best_uci = top_moves[0]["Move"] if top_moves else None
                    played_uci = move.uci()

                    # Check T1/T2/T3
                    top_ucis = [m["Move"] for m in top_moves]
                    if played_uci == top_ucis[0] if len(top_ucis) > 0 else False:
                        stats["t1_matches"] += 1
                        stats["t2_matches"] += 1
                        stats["t3_matches"] += 1
                    elif played_uci in top_ucis[:2]:
                        stats["t2_matches"] += 1
                        stats["t3_matches"] += 1
                    elif played_uci in top_ucis[:3]:
                        stats["t3_matches"] += 1

                    # Calculate centipawn loss
                    board.push(move)
                    engine.set_fen_position(board.fen())
                    engine.set_depth(depth)
                    eval_after = engine.get_evaluation()

                    cp_before = _cp_value(eval_before)
                    cp_after = _cp_value(eval_after)

                    # CPL from the moving side's perspective
                    if board.turn == chess.BLACK:
                        # White just moved
                        cpl = max(0, cp_before - (-cp_after))
                    else:
                        # Black just moved
                        cpl = max(0, (-cp_before) - cp_after)

                    stats["total_cpl"] += cpl
                    stats["total_positions"] += 1
                    stats["phase_stats"][phase]["positions"] += 1
                    stats["phase_stats"][phase]["total_cpl"] += cpl

                    if cpl > 200:
                        stats["blunders"] += 1
                        stats["phase_stats"][phase]["blunders"] += 1
                    elif cpl > 100:
                        stats["mistakes"] += 1
                    elif cpl > 50:
                        stats["inaccuracies"] += 1

                except Exception:
                    board.push(move)
                    continue

            stats["games_analyzed"] += 1

        # Compute derived stats
        total = stats["total_positions"]
        if total > 0:
            stats["acpl"] = round(stats["total_cpl"] / total, 1)
            stats["blunder_rate"] = round(stats["blunders"] / total, 4)
            stats["mistake_rate"] = round(stats["mistakes"] / total, 4)
            stats["inaccuracy_rate"] = round(stats["inaccuracies"] / total, 4)
            stats["t1_accuracy"] = round(stats["t1_matches"] / total, 4)
            stats["t2_accuracy"] = round(stats["t2_matches"] / total, 4)
            stats["t3_accuracy"] = round(stats["t3_matches"] / total, 4)

            for phase_name, ps in stats["phase_stats"].items():
                if ps["positions"] > 0:
                    ps["acpl"] = round(ps["total_cpl"] / ps["positions"], 1)
        else:
            stats["acpl"] = 0
            stats["blunder_rate"] = 0
            stats["t1_accuracy"] = 0

        return stats

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _batch)
