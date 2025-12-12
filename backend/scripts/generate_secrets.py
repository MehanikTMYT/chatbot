"""
Script to generate secure secrets for the AI character communication platform.
This script creates a .env file with all necessary secrets if it doesn't exist.
"""

import os
import secrets
import base64
from pathlib import Path


def generate_secret():
    """Generate a secure random secret key (32 bytes = 256 bits)"""
    return base64.b64encode(secrets.token_bytes(32)).decode('utf-8')


def generate_mysql_url():
    """Generate a MySQL connection URL template"""
    return "mysql+pymysql://ai_platform_user:password@localhost:3306/ai_character_platform"


def generate_smtp_config():
    """Generate SMTP configuration"""
    return {
        'SMTP_USERNAME': 'notifications@ai-platform.local',
        'SMTP_PASSWORD': generate_secret(),  # This would be an app password in real scenario
        'SMTP_SERVER': 'smtp.gmail.com',  # Or your preferred SMTP server
        'SMTP_PORT': '587'
    }


def main():
    """Main function to generate secrets and create .env file"""
    env_file = Path(__file__).parent.parent / '.env'
    env_example_file = Path(__file__).parent.parent / '.env.example'
    
    # Check if .env file already exists
    if env_file.exists():
        print(f"{env_file} already exists. No changes made.")
        return
    
    # Generate secrets
    jwt_secret = generate_secret()
    websocket_secret = generate_secret()
    api_key = generate_secret()
    
    # Generate database URL
    db_url = generate_mysql_url()
    
    # Generate SMTP config
    smtp_config = generate_smtp_config()
    
    # Create .env file content - заменена стрелка ↔ на текстовое обозначение
    env_content = f"""# AI Character Communication Platform - Environment Variables
# Generated automatically by generate_secrets.py

# JWT Configuration
JWT_SECRET={jwt_secret}

# Database Configuration
DATABASE_URL={db_url}

# SMTP Configuration
SMTP_USERNAME={smtp_config['SMTP_USERNAME']}
SMTP_PASSWORD={smtp_config['SMTP_PASSWORD']}
SMTP_SERVER={smtp_config['SMTP_SERVER']}
SMTP_PORT={smtp_config['SMTP_PORT']}

# WebSocket Configuration
WEBSOCKET_SECRET_KEY={websocket_secret}

# Internal API Key for VDS to Local PC communication
INTERNAL_API_KEY={api_key}

# Application Settings
APP_ENVIRONMENT=development
DEBUG=True
SERVER_NAME=localhost
SERVER_HOST=http://localhost
BACKEND_CORS_ORIGINS=["http://localhost", "http://localhost:3000", "https://localhost", "https://localhost:3000", "http://127.0.0.1:5173"]
"""
    
    # Write .env file with explicit UTF-8 encoding
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print(f"✅ Generated {env_file} with secure secrets")
    
    # Create .env.example file with example values
    env_example_content = f"""# AI Character Communication Platform - Environment Variables Template
# DO NOT put real secrets here! This is only a template.

# JWT Configuration
JWT_SECRET=your_strong_jwt_secret_here_base64_encoded_32_bytes

# Database Configuration
DATABASE_URL=mysql+pymysql://username:password@host:port/database_name

# SMTP Configuration (example with Gmail)
SMTP_USERNAME=your.email@gmail.com
SMTP_PASSWORD=your_app_password_here  # Use app password, not account password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# WebSocket Configuration
WEBSOCKET_SECRET_KEY=your_secure_websocket_secret_here_base64_encoded

# Internal API Key for VDS to Local PC communication
INTERNAL_API_KEY=your_strong_internal_api_key_here_base64_encoded

# Application Settings
APP_ENVIRONMENT=development
DEBUG=True
SERVER_NAME=localhost
SERVER_HOST=http://localhost
BACKEND_CORS_ORIGINS=["http://localhost", "http://localhost:3000", "https://localhost", "https://localhost:3000", "http://127.0.0.1:5173"]
"""
    
    # Write .env.example file with explicit UTF-8 encoding
    with open(env_example_file, 'w', encoding='utf-8') as f:
        f.write(env_example_content)
    
    print(f"✅ Generated {env_example_file} as template")
    
    # Create .gitignore if it doesn't exist
    gitignore_file = Path(__file__).parent.parent / '.gitignore'
    if not gitignore_file.exists():
        gitignore_content = """# .gitignore
# Environment variables
.env
*.env

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
.venv/
venv/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Databases
*.sqlite3
*.db

# Logs
*.log

# OS
.DS_Store
Thumbs.db

# Build
build/
dist/
*.egg-info/
"""
        with open(gitignore_file, 'w', encoding='utf-8') as f:
            f.write(gitignore_content)
        print(f"✅ Generated {gitignore_file}")


if __name__ == "__main__":
    main()