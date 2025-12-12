# AI Character Communication Platform - Backend

Backend service for the AI character communication platform built with FastAPI.

## Features

- Secure JWT-based authentication
- Real-time communication via WebSockets
- Integration with local AI models
- Secure environment management

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Generate environment secrets:
```bash
python scripts/generate_secrets.py
```

3. Run the development server:
```bash
uvicorn app.main:app --reload --port 8000
```

## Endpoints

- `GET /api/health` - Health check
- `GET /docs` - Interactive API documentation

## Security

All sensitive data is stored in environment variables. The `.env` file is automatically generated with secure secrets and is excluded from version control.