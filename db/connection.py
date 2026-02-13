"""Async PostgreSQL connection pool using asyncpg.

All connections use the 'chesscode' schema by default.
"""
import os

_pool = None

# Dedicated schema name
SCHEMA = "chesscode"


async def _init_connection(conn):
    """Set search_path to chesscode schema on each new connection."""
    await conn.execute(f"SET search_path TO {SCHEMA}, public")


async def get_pool():
    """Get or create the asyncpg connection pool.

    Every connection automatically uses the 'chesscode' schema.
    """
    global _pool
    if _pool is None:
        try:
            import asyncpg
        except ImportError:
            raise RuntimeError(
                "asyncpg not installed. Run: pip install asyncpg"
            )
        dsn = os.getenv(
            "DB_URL",
            "postgresql://postgres:postgres@localhost:5432/chesscode",
        )
        _pool = await asyncpg.create_pool(
            dsn=dsn,
            min_size=2,
            max_size=10,
            init=_init_connection,
        )
    return _pool


async def close_pool():
    """Close the connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
