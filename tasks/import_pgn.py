"""Import PGN files into PostgreSQL database.

Usage:
    python -m tasks.import_pgn [--data-dir data] [--file specific_file.pgn]
"""
import asyncio
import os
import sys
from pathlib import Path
from datetime import date as date_type

import chess.pgn
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.pgn_tools import load_pgn_file, game_to_dict, ENCODINGS


async def import_pgn_file(filepath: str, pool) -> int:
    """Import a single PGN file into the database. Returns number of games imported."""
    source = os.path.basename(filepath)
    print(f"Importing {source}...")

    games = load_pgn_file(filepath)
    imported = 0

    for game in games:
        try:
            headers = dict(game.headers)
            gd = game_to_dict(game)

            # Parse date
            game_date = None
            date_str = headers.get("Date", "")
            if date_str and date_str != "????.??.??":
                parts = date_str.replace("?", "1").split(".")
                if len(parts) == 3:
                    try:
                        game_date = date_type(int(parts[0]), int(parts[1]), int(parts[2]))
                    except ValueError:
                        pass

            # Parse ELO
            white_elo = None
            black_elo = None
            try:
                we = headers.get("WhiteElo", "")
                if we and we.isdigit():
                    white_elo = int(we)
            except (ValueError, TypeError):
                pass
            try:
                be = headers.get("BlackElo", "")
                if be and be.isdigit():
                    black_elo = int(be)
            except (ValueError, TypeError):
                pass

            # Build PGN text
            pgn_text = str(game)

            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO games (source_file, event, site, date, round,
                                       white, black, result, white_elo, black_elo,
                                       eco, pgn_text, moves_san, move_count)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                    ON CONFLICT DO NOTHING
                    """,
                    source,
                    headers.get("Event", ""),
                    headers.get("Site", ""),
                    game_date,
                    headers.get("Round", ""),
                    headers.get("White", ""),
                    headers.get("Black", ""),
                    headers.get("Result", ""),
                    white_elo,
                    black_elo,
                    headers.get("ECO", ""),
                    pgn_text,
                    gd.get("moves_san", ""),
                    gd.get("move_count", 0),
                )
                imported += 1

        except Exception as e:
            print(f"  Warning: Failed to import game: {e}")
            continue

        if imported % 100 == 0 and imported > 0:
            print(f"  Imported {imported} games...")

    print(f"  Done: {imported} games from {source}")
    return imported


async def main():
    """Import all PGN files from the data directory."""
    load_dotenv()

    import argparse
    parser = argparse.ArgumentParser(description="Import PGN files into PostgreSQL")
    parser.add_argument("--data-dir", default="data", help="Directory containing PGN files")
    parser.add_argument("--file", help="Import a specific PGN file")
    parser.add_argument("--create-schema", action="store_true", help="Create database schema first")
    args = parser.parse_args()

    # Connect to database
    try:
        from db.connection import get_pool, close_pool
        pool = await get_pool()
    except Exception as e:
        print(f"Error connecting to database: {e}")
        print("Make sure PostgreSQL is running and DB_URL is set in .env")
        return

    # Optionally create schema
    if args.create_schema:
        from db.schema import create_schema
        await create_schema(pool)

    # Import files
    total = 0
    if args.file:
        total = await import_pgn_file(args.file, pool)
    else:
        data_dir = Path(args.data_dir)
        for pgn_path in sorted(data_dir.glob("*.pgn")):
            count = await import_pgn_file(str(pgn_path), pool)
            total += count

    print(f"\nTotal games imported: {total}")

    await close_pool()


if __name__ == "__main__":
    asyncio.run(main())
