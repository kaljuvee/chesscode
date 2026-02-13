"""Database CRUD operations for games, labels, players, and students."""
from typing import List, Dict, Optional
from datetime import datetime

from .connection import get_pool


# --- Games ---

async def store_game(game_data: Dict) -> Optional[int]:
    """Insert a game into the database. Returns the game ID."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchval(
            """
            INSERT INTO games (source_file, event, site, date, round, white, black,
                               result, white_elo, black_elo, eco, pgn_text,
                               moves_san, move_count)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            ON CONFLICT DO NOTHING
            RETURNING id
            """,
            game_data.get("source_file", ""),
            game_data.get("event", ""),
            game_data.get("site", ""),
            game_data.get("date"),
            game_data.get("round", ""),
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


async def get_game(game_id: int) -> Optional[Dict]:
    """Retrieve a game by ID."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM games WHERE id = $1", game_id)
        return dict(row) if row else None


async def search_games(
    player: str = None,
    eco: str = None,
    result: str = None,
    limit: int = 50,
) -> List[Dict]:
    """Search games with filters."""
    pool = await get_pool()
    conditions = []
    params = []
    idx = 1

    if player:
        conditions.append(f"(white ILIKE ${idx} OR black ILIKE ${idx})")
        params.append(f"%{player}%")
        idx += 1

    if eco:
        conditions.append(f"eco LIKE ${idx}")
        params.append(f"{eco}%")
        idx += 1

    if result:
        conditions.append(f"result = ${idx}")
        params.append(result)
        idx += 1

    where = " AND ".join(conditions) if conditions else "TRUE"
    params.append(limit)

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            f"SELECT * FROM games WHERE {where} ORDER BY date DESC LIMIT ${idx}",
            *params,
        )
        return [dict(row) for row in rows]


# --- Labels ---

async def add_label(
    game_id: int,
    label_type: str,
    label_value: str,
    position_fen: str = None,
    move_number: int = None,
    created_by: str = "admin",
) -> Optional[int]:
    """Add a label/mask to a game or specific position."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchval(
            """
            INSERT INTO game_labels (game_id, label_type, label_value,
                                     position_fen, move_number, created_by)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
            """,
            game_id, label_type, label_value, position_fen, move_number, created_by,
        )


async def get_labels(game_id: int) -> List[Dict]:
    """Get all labels for a game."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM game_labels WHERE game_id = $1 ORDER BY move_number",
            game_id,
        )
        return [dict(row) for row in rows]


async def search_by_label(
    label_type: str = None,
    label_value: str = None,
    limit: int = 20,
) -> List[Dict]:
    """Search games by their labels."""
    pool = await get_pool()
    conditions = []
    params = []
    idx = 1

    if label_type:
        conditions.append(f"gl.label_type = ${idx}")
        params.append(label_type)
        idx += 1

    if label_value:
        conditions.append(f"gl.label_value ILIKE ${idx}")
        params.append(f"%{label_value}%")
        idx += 1

    where = " AND ".join(conditions) if conditions else "TRUE"
    params.append(limit)

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            f"""
            SELECT g.*, gl.label_type, gl.label_value, gl.position_fen, gl.move_number
            FROM games g
            JOIN game_labels gl ON g.id = gl.game_id
            WHERE {where}
            ORDER BY g.date DESC
            LIMIT ${idx}
            """,
            *params,
        )
        return [dict(row) for row in rows]


# --- Player Stats ---

async def upsert_player_stats(stats: Dict) -> Optional[int]:
    """Insert or update player statistics."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchval(
            """
            INSERT INTO player_stats (player_name, total_games, wins, draws, losses,
                                      avg_cpl, blunder_rate, t1_accuracy,
                                      most_played_eco, analyzed_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            ON CONFLICT (player_name) DO UPDATE SET
                total_games = EXCLUDED.total_games,
                wins = EXCLUDED.wins,
                draws = EXCLUDED.draws,
                losses = EXCLUDED.losses,
                avg_cpl = EXCLUDED.avg_cpl,
                blunder_rate = EXCLUDED.blunder_rate,
                t1_accuracy = EXCLUDED.t1_accuracy,
                most_played_eco = EXCLUDED.most_played_eco,
                analyzed_at = EXCLUDED.analyzed_at
            RETURNING id
            """,
            stats.get("player_name", ""),
            stats.get("total_games", 0),
            stats.get("wins", 0),
            stats.get("draws", 0),
            stats.get("losses", 0),
            stats.get("avg_cpl"),
            stats.get("blunder_rate"),
            stats.get("t1_accuracy"),
            stats.get("most_played_eco"),
            stats.get("analyzed_at", datetime.now()),
        )


# --- Student Profiles ---

async def get_student_profile(username: str) -> Optional[Dict]:
    """Get a student profile by username."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM student_profiles WHERE username = $1", username
        )
        return dict(row) if row else None


async def upsert_student_profile(profile: Dict) -> Optional[int]:
    """Insert or update a student profile."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        import json
        weaknesses_json = json.dumps(profile.get("weaknesses", {}))
        return await conn.fetchval(
            """
            INSERT INTO student_profiles (username, estimated_rating, weaknesses, last_assessed)
            VALUES ($1, $2, $3::jsonb, $4)
            ON CONFLICT (username) DO UPDATE SET
                estimated_rating = EXCLUDED.estimated_rating,
                weaknesses = EXCLUDED.weaknesses,
                last_assessed = EXCLUDED.last_assessed
            RETURNING id
            """,
            profile.get("username", ""),
            profile.get("estimated_rating"),
            weaknesses_json,
            profile.get("last_assessed", datetime.now()),
        )
