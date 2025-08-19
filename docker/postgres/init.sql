-- Counter-Strike AG2 Database Schema
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Game Sessions Table
CREATE TABLE game_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_name VARCHAR(255) NOT NULL,
    max_rounds INTEGER DEFAULT 3,
    current_round INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Game State Table
CREATE TABLE game_states (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES game_sessions(id) ON DELETE CASCADE,
    round_number INTEGER NOT NULL,
    phase VARCHAR(50) DEFAULT 'chat',
    bomb_planted BOOLEAN DEFAULT FALSE,
    bomb_site VARCHAR(50),
    winner VARCHAR(50),
    round_time INTEGER DEFAULT 120,
    bomb_timer INTEGER DEFAULT 40,
    state_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Player Health and Positions
CREATE TABLE player_states (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES game_sessions(id) ON DELETE CASCADE,
    round_number INTEGER NOT NULL,
    team VARCHAR(50) NOT NULL,
    player_name VARCHAR(100) NOT NULL,
    health INTEGER DEFAULT 100,
    position VARCHAR(50) DEFAULT 'spawn',
    is_alive BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Game Actions Log
CREATE TABLE game_actions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES game_sessions(id) ON DELETE CASCADE,
    round_number INTEGER NOT NULL,
    team VARCHAR(50) NOT NULL,
    player_name VARCHAR(100) NOT NULL,
    action VARCHAR(255) NOT NULL,
    result TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI Agent Interactions
CREATE TABLE agent_interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES game_sessions(id) ON DELETE CASCADE,
    agent_type VARCHAR(100) NOT NULL,
    query TEXT NOT NULL,
    response TEXT,
    context_data JSONB,
    processing_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Round Scores
CREATE TABLE round_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES game_sessions(id) ON DELETE CASCADE,
    round_number INTEGER NOT NULL,
    terrorists_score INTEGER DEFAULT 0,
    counter_terrorists_score INTEGER DEFAULT 0,
    round_winner VARCHAR(50),
    round_end_reason VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_game_states_session_round ON game_states(session_id, round_number);
CREATE INDEX idx_player_states_session_round ON player_states(session_id, round_number);
CREATE INDEX idx_game_actions_session_round ON game_actions(session_id, round_number);
CREATE INDEX idx_agent_interactions_session ON agent_interactions(session_id);
CREATE INDEX idx_round_scores_session ON round_scores(session_id);

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_game_sessions_updated_at BEFORE UPDATE ON game_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_player_states_updated_at BEFORE UPDATE ON player_states FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
