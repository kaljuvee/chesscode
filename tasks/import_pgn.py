"""Import PGN files into PostgreSQL database.

Usage:
    python -m tasks.import_pgn [--data-dir data] [--file specific_file.pgn]

Uses streaming PGN parsing for memory efficiency with large files.
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

# Encodings to try
ENCODINGS = ["utf-8", "latin-1", "iso-8859-1", "cp1252"]


def _parse_date(date_str: str):
    """Parse a PGN date string into a date object."""
    if not date_str or date_str == "????.??.??":
        return None
    parts = date_str.replace("?", "1").split(".")
    if len(parts) == 3:
        try:
            return date_type(int(parts[0]), int(parts[1]), int(parts[2]))
        except ValueError:
            return None
    return None


def _parse_elo(elo_str: str):
    """Parse an ELO string into an integer."""
    if elo_str and elo_str.isdigit():
        return int(elo_str)
    return None


async def import_pgn_file(filepath: str, pool) -> int:
    """Import a single PGN file using streaming parser (one game at a time)."""
    source = os.path.basename(filepath)
    print(f"Importing {source}...", flush=True)

    imported = 0
    errors = 0

    # Try different encodings
    for encoding in ENCODINGS:
        try:
            f = open(filepath, "r", encoding=encoding)
            # Test reading a line
            f.readline()
            f.seek(0)
            break
        except UnicodeDecodeError:
            f.close()
            continue
    else:
        print(f"  ERROR: Cannot read {source} with any encoding")
        return 0

    async with pool.acquire() as conn:
        await conn.execute("SET search_path TO chesscode, public")

        while True:
            try:
                game = chess.pgn.read_game(f)
            except Exception:
                continue

            if game is None:
                break

            try:
                headers = dict(game.headers)
                game_date = _parse_date(headers.get("Date", ""))
                white_elo = _parse_elo(headers.get("WhiteElo", ""))
                black_elo = _parse_elo(headers.get("BlackElo", ""))

                # Get moves in SAN
                moves_san = []
                board = game.board()
                for move in game.mainline_moves():
                    moves_san.append(board.san(move))
                    board.push(move)

                pgn_text = str(game)

                await conn.execute(
                    """
                    INSERT INTO chesscode.games (source_file, event, site, date, round,
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
                    " ".join(moves_san),
                    len(moves_san),
                )
                imported += 1

            except Exception as e:
                errors += 1
                if errors <= 3:
                    print(f"  Warning: {e}", flush=True)
                continue

            if imported % 500 == 0 and imported > 0:
                print(f"  {source}: {imported} games imported...", flush=True)

    f.close()
    print(f"  Done: {imported} games from {source} ({errors} errors)", flush=True)
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

    print(f"\nTotal games imported: {total}", flush=True)

    await close_pool()


if __name__ == "__main__":
    asyncio.run(main())
