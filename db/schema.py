"""Database schema creation and migration.

All tables live in the 'chesscode' schema.
"""
from pathlib import Path

from .connection import SCHEMA


async def create_schema(pool=None):
    """Create the database schema from schema_v2.sql.

    If pool is None, creates a new connection pool.
    """
    if pool is None:
        from .connection import get_pool
        pool = await get_pool()

    schema_path = Path(__file__).parent.parent / "sql" / "schema_v2.sql"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    sql = schema_path.read_text()

    async with pool.acquire() as conn:
        await conn.execute(sql)

    print(f"Database schema '{SCHEMA}' created successfully.")


async def drop_schema(pool=None):
    """Drop all tables in the chesscode schema (use with caution)."""
    if pool is None:
        from .connection import get_pool
        pool = await get_pool()

    async with pool.acquire() as conn:
        await conn.execute(f"""
            DROP TABLE IF EXISTS {SCHEMA}.game_labels CASCADE;
            DROP TABLE IF EXISTS {SCHEMA}.game_embeddings CASCADE;
            DROP TABLE IF EXISTS {SCHEMA}.book_chapters CASCADE;
            DROP TABLE IF EXISTS {SCHEMA}.student_profiles CASCADE;
            DROP TABLE IF EXISTS {SCHEMA}.player_stats CASCADE;
            DROP TABLE IF EXISTS {SCHEMA}.openings CASCADE;
            DROP TABLE IF EXISTS {SCHEMA}.games CASCADE;
        """)

    print(f"Database schema '{SCHEMA}' tables dropped.")
