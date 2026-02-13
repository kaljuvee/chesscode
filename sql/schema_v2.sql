-- ChessCode v2 Database Schema
-- Uses dedicated 'chesscode' schema (not public)

-- Create dedicated schema
CREATE SCHEMA IF NOT EXISTS chesscode;

-- Enable pgvector extension (requires superuser, may already exist)
CREATE EXTENSION IF NOT EXISTS vector;

-- Set search path for this session
SET search_path TO chesscode, public;

-- Games table: one row per game from PGN files
CREATE TABLE IF NOT EXISTS chesscode.games (
    id SERIAL PRIMARY KEY,
    source_file VARCHAR(255) NOT NULL DEFAULT '',
    event VARCHAR(255),
    site VARCHAR(255),
    date DATE,
    round VARCHAR(50),
    white VARCHAR(255) NOT NULL,
    black VARCHAR(255) NOT NULL,
    result VARCHAR(10),                     -- '1-0', '0-1', '1/2-1/2', '*'
    white_elo INTEGER,
    black_elo INTEGER,
    eco VARCHAR(10),                        -- ECO opening code
    pgn_text TEXT NOT NULL DEFAULT '',      -- Full PGN text of the game
    moves_san TEXT,                         -- Space-separated SAN moves
    move_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(white, black, date, round, event)
);

-- Game labels and masks (PGN annotations, NAGs, position tags)
CREATE TABLE IF NOT EXISTS chesscode.game_labels (
    id SERIAL PRIMARY KEY,
    game_id INTEGER REFERENCES chesscode.games(id) ON DELETE CASCADE,
    label_type VARCHAR(50) NOT NULL,        -- 'nag', 'comment', 'opening', 'theme',
                                            -- 'mask', 'tactic', 'endgame', 'custom'
    label_value TEXT NOT NULL,              -- e.g. '$1', 'Brilliant sacrifice',
                                            -- 'pin', 'rook_endgame'
    position_fen VARCHAR(100),              -- FEN of specific position (NULL = whole game)
    move_number INTEGER,                    -- Half-move number (NULL = whole game)
    created_by VARCHAR(50) DEFAULT 'admin', -- 'admin', 'engine', 'auto', 'student'
    created_at TIMESTAMP DEFAULT NOW()
);

-- Embeddings table: vector representations of games for semantic search
CREATE TABLE IF NOT EXISTS chesscode.game_embeddings (
    id SERIAL PRIMARY KEY,
    game_id INTEGER REFERENCES chesscode.games(id) ON DELETE CASCADE,
    embedding vector(3072),                 -- text-embedding-3-large dimension
    description TEXT NOT NULL,              -- Text that was embedded
    model VARCHAR(100) NOT NULL,            -- Embedding model name
    created_at TIMESTAMP DEFAULT NOW()
);

-- Player statistics cache
CREATE TABLE IF NOT EXISTS chesscode.player_stats (
    id SERIAL PRIMARY KEY,
    player_name VARCHAR(255) NOT NULL UNIQUE,
    total_games INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    draws INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    avg_cpl FLOAT,                          -- Average centipawn loss
    blunder_rate FLOAT,
    t1_accuracy FLOAT,                      -- Top-1 engine move match rate
    most_played_eco VARCHAR(10),
    analyzed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Openings reference table
CREATE TABLE IF NOT EXISTS chesscode.openings (
    id SERIAL PRIMARY KEY,
    eco VARCHAR(10) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    moves_san TEXT,                         -- Defining move sequence
    fen VARCHAR(255),                       -- Position after the opening moves
    description TEXT
);

-- Student profiles for personal teacher agent
CREATE TABLE IF NOT EXISTS chesscode.student_profiles (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    estimated_rating INTEGER,
    weaknesses JSONB,                       -- {"tactics": 0.6, "endgames": 0.3, ...}
    last_assessed TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Book content for children's coach (framework for future content)
CREATE TABLE IF NOT EXISTS chesscode.book_chapters (
    id SERIAL PRIMARY KEY,
    book_title VARCHAR(255),
    chapter_number INTEGER,
    chapter_title VARCHAR(255),
    content TEXT,
    difficulty_level INTEGER DEFAULT 1,     -- 1=beginner, 2=intermediate, 3=advanced
    topics JSONB,                           -- ["pins", "forks", "discovered_attack"]
    embedding vector(3072),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_games_white ON chesscode.games(white);
CREATE INDEX IF NOT EXISTS idx_games_black ON chesscode.games(black);
CREATE INDEX IF NOT EXISTS idx_games_eco ON chesscode.games(eco);
CREATE INDEX IF NOT EXISTS idx_games_date ON chesscode.games(date);
CREATE INDEX IF NOT EXISTS idx_games_source ON chesscode.games(source_file);

CREATE INDEX IF NOT EXISTS idx_labels_game ON chesscode.game_labels(game_id);
CREATE INDEX IF NOT EXISTS idx_labels_type ON chesscode.game_labels(label_type);
CREATE INDEX IF NOT EXISTS idx_labels_type_value ON chesscode.game_labels(label_type, label_value);

-- Vector indexes (HNSW for fast approximate nearest neighbor search)
-- Only create these after populating data
-- CREATE INDEX idx_game_embeddings_hnsw ON chesscode.game_embeddings
--     USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
-- CREATE INDEX idx_book_embeddings_hnsw ON chesscode.book_chapters
--     USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
