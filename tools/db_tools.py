"""PostgreSQL + pgvector database tools.

Provides async database operations for game storage, search, and embeddings.
Requires a running PostgreSQL instance with pgvector extension.
"""
import os
from typing import List, Dict, Optional


async def _get_pool():
    """Get the database connection pool (lazy import to avoid hard dependency)."""
    try:
        from db.connection import get_pool
        return await get_pool()
    except Exception:
        return None


async def semantic_search(query: str, limit: int = 5) -> List[Dict]:
    """Search games using pgvector semantic similarity.

    Requires embeddings to be populated in game_embeddings table.
    Returns matching games with similarity scores.
    """
    pool = await _get_pool()
    if pool is None:
        return []

    try:
        # This requires an embedding of the query first
        # For now, fall back to text search
        return await text_search(query, limit)
    except Exception:
        return []


async def text_search(query: str, limit: int = 10) -> List[Dict]:
    """Full-text search over game metadata."""
    pool = await _get_pool()
    if pool is None:
        return []

    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, white, black, result, eco, date, event, site
                FROM games
                WHERE white ILIKE $1 OR black ILIKE $1
                   OR event ILIKE $1 OR eco ILIKE $2
                ORDER BY date DESC
                LIMIT $3
                """,
                f"%{query}%",
                query.upper(),
                limit,
            )
            return [dict(row) for row in rows]
    except Exception:
        return []


async def search_by_eco(eco: str, limit: int = 20) -> List[Dict]:
    """Search games by ECO opening code."""
    pool = await _get_pool()
    if pool is None:
        return []

    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, white, black, result, eco, date, event, moves_san
                FROM games
                WHERE eco LIKE $1
                ORDER BY date DESC
                LIMIT $2
                """,
                f"{eco}%",
                limit,
            )
            return [dict(row) for row in rows]
    except Exception:
        return []


async def search_by_player(player: str, limit: int = 50) -> List[Dict]:
    """Search games by player name (White or Black)."""
    pool = await _get_pool()
    if pool is None:
        return []

    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, white, black, result, eco, date, event, moves_san
                FROM games
                WHERE white ILIKE $1 OR black ILIKE $1
                ORDER BY date DESC
                LIMIT $2
                """,
                f"%{player}%",
                limit,
            )
            return [dict(row) for row in rows]
    except Exception:
        return []


async def store_game(game_data: Dict, embedding: List[float] = None) -> Optional[int]:
    """Store a parsed game in the database with optional embedding."""
    pool = await _get_pool()
    if pool is None:
        return None

    try:
        async with pool.acquire() as conn:
            game_id = await conn.fetchval(
                """
                INSERT INTO games (source_file, event, site, date, white, black,
                                   result, white_elo, black_elo, eco, pgn_text,
                                   moves_san, move_count)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                ON CONFLICT DO NOTHING
                RETURNING id
                """,
                game_data.get("source_file", ""),
                game_data.get("event", ""),
                game_data.get("site", ""),
                game_data.get("date"),
                game_data.get("white", ""),
                game_data.get("black", ""),
                game_data.get("result", ""),
                game_data.get("white_elo"),
                game_data.get("black_elo"),
                game_data.get("eco", ""),
                game_data.get("pgn_text", ""),
                game_data.get("moves_san", ""),
                game_data.get("move_count", 0),
            )
            return game_id
    except Exception:
        return None


async def get_game_by_id(game_id: int) -> Optional[Dict]:
    """Retrieve a game by its database ID."""
    pool = await _get_pool()
    if pool is None:
        return None

    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM games WHERE id = $1", game_id
            )
            return dict(row) if row else None
    except Exception:
        return None


async def add_label(game_id: int, label_type: str, label_value: str,
                    position_fen: str = None, move_number: int = None) -> Optional[int]:
    """Add a label or mask to a game or specific position.

    Supports PGN-style labels: NAG codes, position comments, opening tags, etc.
    """
    pool = await _get_pool()
    if pool is None:
        return None

    try:
        async with pool.acquire() as conn:
            label_id = await conn.fetchval(
                """
                INSERT INTO game_labels (game_id, label_type, label_value,
                                         position_fen, move_number)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
                """,
                game_id, label_type, label_value, position_fen, move_number,
            )
            return label_id
    except Exception:
        return None


async def search_by_label(label_type: str = None, label_value: str = None,
                          limit: int = 20) -> List[Dict]:
    """Search games by their labels/masks."""
    pool = await _get_pool()
    if pool is None:
        return []

    try:
        async with pool.acquire() as conn:
            if label_type and label_value:
                rows = await conn.fetch(
                    """
                    SELECT g.*, gl.label_type, gl.label_value, gl.position_fen
                    FROM games g
                    JOIN game_labels gl ON g.id = gl.game_id
                    WHERE gl.label_type = $1 AND gl.label_value ILIKE $2
                    LIMIT $3
                    """,
                    label_type, f"%{label_value}%", limit,
                )
            elif label_type:
                rows = await conn.fetch(
                    """
                    SELECT g.*, gl.label_type, gl.label_value, gl.position_fen
                    FROM games g
                    JOIN game_labels gl ON g.id = gl.game_id
                    WHERE gl.label_type = $1
                    LIMIT $2
                    """,
                    label_type, limit,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT g.*, gl.label_type, gl.label_value, gl.position_fen
                    FROM games g
                    JOIN game_labels gl ON g.id = gl.game_id
                    LIMIT $1
                    """,
                    limit,
                )
            return [dict(row) for row in rows]
    except Exception:
        return []
