-- Database initialization script for Hybrid Chatbot System
-- This script will run on first startup of the PostgreSQL container

-- Create tables for the chatbot system
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    title VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL, -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);

-- Insert default admin user (change password in production!)
-- INSERT INTO users (username, email, hashed_password) 
-- VALUES ('admin', 'admin@example.com', '$2b$12$KIXB0mVei9Uq65W9.iGIXuqC6OxHmF15l.v8M6ufPx.dKjV5h8eIe'); -- password: admin123

-- Grant permissions (if needed)
GRANT ALL PRIVILEGES ON TABLE users TO chatbot_user;
GRANT ALL PRIVILEGES ON TABLE conversations TO chatbot_user;
GRANT ALL PRIVILEGES ON TABLE messages TO chatbot_user;

-- Grant sequence permissions for auto-incrementing primary keys
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO chatbot_user;