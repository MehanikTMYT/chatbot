# Hybrid Chatbot System

A comprehensive chatbot system with multimodal capabilities, supporting text, voice, and document interactions.

## Features

- Multimodal interaction (text, voice, documents)
- Context-aware conversations
- Web search integration
- LLM-powered responses
- Secure authentication and authorization
- Scalable microservices architecture

## Deployment

The system can be deployed in multiple ways depending on your needs:

### Docker Deployment (Recommended)

For easy deployment on various platforms (PC, VDS, cloud servers):

1. **Prerequisites**:
   - Docker (version 20.10 or higher)
   - Docker Compose (version 2.0 or higher)

2. **Configuration**:
   ```bash
   cp .env.example .env
   # Edit .env to match your environment requirements
   ```

3. **Build and Run**:
   ```bash
   ./build-docker.sh
   docker-compose up -d
   ```

For detailed Docker deployment instructions, see [DOCKER-README.md](DOCKER-README.md).

### Direct Installation

See individual component README files in their respective directories for direct installation instructions.

## Architecture

The system consists of several interconnected components:

- **Context Manager**: Manages conversation history and context
- **LLM Worker**: Processes requests with large language models
- **Web Worker**: Handles web search and information retrieval
- **Backend API**: Main application logic and data management
- **Frontend UI**: User interface for interaction

## Contributing

Feel free to contribute to the project by submitting issues or pull requests.

## License

See the LICENSE file for licensing information.