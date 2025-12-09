# Secure Web Worker for Windows 11

This project implements a secure Web Worker for safe internet access with comprehensive content filtering and protection against malicious content. The system provides safe search capabilities for AI characters while maintaining privacy and security.

## Features

- Secure web requests with proxy support
- Content filtering at multiple levels (domains, keywords, ML-based)
- Integration with DuckDuckGo API and fallback sources
- Character safety restrictions
- Request caching and rate limiting
- Network resource monitoring
- Windows 11 compatibility

## Architecture

The system consists of:
- Web Worker core with async HTTP requests
- Security filtering layers
- Character permission system
- Request caching and rate limiting
- Network monitoring components

## Installation

1. Install dependencies:
```bash
pip install requests aiohttp beautifulsoup4 tldextract cryptography
```

2. Set up configuration in `config/config.py`

3. Run the web worker:
```bash
python src/python/web_worker.py
```

## Usage

The web worker provides endpoints for:
- Secure search queries
- Content retrieval
- Permission management
- Request monitoring