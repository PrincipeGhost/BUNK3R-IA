CREATE_AI_CHAT_SQL = """
-- ============================================================
-- SISTEMA DE CHAT CON IA - PERSISTENCIA
-- ============================================================

CREATE TABLE IF NOT EXISTS ai_chat_messages (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    provider VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ai_chat_user ON ai_chat_messages(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_chat_created ON ai_chat_messages(created_at DESC);

CREATE TABLE IF NOT EXISTS ai_chat_sessions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    title VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ai_sessions_user ON ai_chat_sessions(user_id);

CREATE TABLE IF NOT EXISTS ai_provider_usage (
    id SERIAL PRIMARY KEY,
    provider VARCHAR(50) NOT NULL,
    user_id VARCHAR(255),
    request_count INTEGER DEFAULT 0,
    tokens_used INTEGER DEFAULT 0,
    usage_date DATE DEFAULT CURRENT_DATE,
    UNIQUE(provider, user_id, usage_date)
);

CREATE INDEX IF NOT EXISTS idx_ai_usage_provider ON ai_provider_usage(provider);
CREATE INDEX IF NOT EXISTS idx_ai_usage_date ON ai_provider_usage(usage_date);
"""
