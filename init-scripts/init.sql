-- Database initialization script for Hybrid Chatbot System
-- This script will run on first startup of the MySQL container

-- Create tables for the chatbot system
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(100),
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS conversations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    user_id INT NOT NULL,
    character_id INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    conversation_id INT NOT NULL,
    sender_type VARCHAR(20) NOT NULL, -- 'user' or 'bot'
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS characters (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    system_prompt TEXT,
    creator_id INT NOT NULL, -- Who created it
    owner_id INT NOT NULL, -- Who owns it
    is_public BOOLEAN DEFAULT FALSE, -- Whether other users can access
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    metadata JSON, -- Additional character metadata
    FOREIGN KEY (creator_id) REFERENCES users(id),
    FOREIGN KEY (owner_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS workers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    worker_id VARCHAR(100) UNIQUE NOT NULL, -- Unique ID for the worker
    name VARCHAR(100) NOT NULL,
    host VARCHAR(100) NOT NULL,
    port INT NOT NULL,
    gpu_model VARCHAR(100), -- e.g., "NVIDIA RTX 4070"
    gpu_memory INT, -- in MB
    total_memory INT, -- in MB
    cpu_count INT,
    status VARCHAR(20) DEFAULT 'offline', -- Use enum values
    last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    capabilities JSON, -- What the worker can do (LLM, web search, etc.)
    performance_metrics JSON -- Performance statistics
);

CREATE TABLE IF NOT EXISTS tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id VARCHAR(100) UNIQUE NOT NULL, -- UUID
    task_type VARCHAR(50) NOT NULL, -- 'llm_inference', 'web_search', etc.
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    priority INT DEFAULT 0, -- Higher number = higher priority
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    assigned_worker_id INT NULL,
    input_data JSON,
    result_data JSON,
    error_message TEXT,
    FOREIGN KEY (assigned_worker_id) REFERENCES workers(id)
);

CREATE TABLE IF NOT EXISTS vector_storage (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL, -- Name of the vector table
    description TEXT,
    dimension INT NOT NULL, -- Vector dimension
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    metadata JSON -- Additional vector storage metadata
);

CREATE TABLE IF NOT EXISTS system_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_workers_worker_id ON workers(worker_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_worker ON tasks(assigned_worker_id);

-- Insert default admin user (change password in production!)
-- INSERT INTO users (username, email, hashed_password) 
-- VALUES ('admin', 'admin@example.com', '$2b$12$KIXB0mVei9Uq65W9.iGIXuqC6OxHmF15l.v8M6ufPx.dKjV5h8eIe'); -- password: admin123