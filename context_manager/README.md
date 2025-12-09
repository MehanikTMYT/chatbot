# Advanced Context Management System

This system implements advanced context management with semantic compression, vector memory, and interactive dialog management. It provides efficient use of LLM context windows, preservation of important information between sessions, and semantic search capabilities.

## Features

- Semantic compression of context with clustering algorithms
- Vector memory with LanceDB for storing and searching dialog history
- Interactive context management UI
- Automatic importance evaluation of messages
- Hybrid search (semantic + keyword)
- Character-specific memory integration
- Performance optimization for Windows workers

## Architecture

The system consists of:
- Python backend with semantic processing and vector storage
- Rust components for performance-critical operations
- TypeScript frontend components for context management
- Integration with LLM and Web workers