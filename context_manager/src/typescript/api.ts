/**
 * API client for context management system
 * Provides methods to interact with the backend context management services
 */

import { Message, ContextSession, SearchResults, CompressionOptions, SearchOptions } from './types';

class ContextAPI {
  private baseUrl: string;
  
  constructor(baseUrl: string = '/api/context') {
    this.baseUrl = baseUrl;
  }
  
  /**
   * Add a message to the context memory
   */
  async addMessage(message: Omit<Message, 'id'>): Promise<string> {
    const response = await fetch(`${this.baseUrl}/message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(message),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to add message: ${response.statusText}`);
    }
    
    return response.text();
  }
  
  /**
   * Add multiple messages to the context memory
   */
  async addMessages(messages: Omit<Message, 'id'>[], characterId?: string, userId?: string): Promise<string[]> {
    const response = await fetch(`${this.baseUrl}/messages`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        messages,
        characterId,
        userId
      }),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to add messages: ${response.statusText}`);
    }
    
    return response.json();
  }
  
  /**
   * Compress the current context
   */
  async compressContext(messages: Message[], options: CompressionOptions = {}): Promise<Message[]> {
    const response = await fetch(`${this.baseUrl}/compress`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        messages,
        ...options
      }),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to compress context: ${response.statusText}`);
    }
    
    const result = await response.json();
    return result.compressedMessages;
  }
  
  /**
   * Perform semantic search in the context memory
   */
  async semanticSearch(query: string, options: SearchOptions = {}): Promise<SearchResults> {
    const params = new URLSearchParams();
    params.append('query', query);
    
    if (options.characterId) params.append('characterId', options.characterId);
    if (options.userId) params.append('userId', options.userId);
    if (options.limit) params.append('limit', options.limit.toString());
    if (options.minImportance) params.append('minImportance', options.minImportance.toString());
    if (options.keywordFilter) params.append('keywordFilter', options.keywordFilter);
    
    const response = await fetch(`${this.baseUrl}/search?${params.toString()}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error(`Failed to search memory: ${response.statusText}`);
    }
    
    return response.json();
  }
  
  /**
   * Perform hybrid search (semantic + keyword) in the context memory
   */
  async hybridSearch(query: string, keywordFilter?: string, options: SearchOptions = {}): Promise<SearchResults> {
    const params = new URLSearchParams();
    params.append('query', query);
    
    if (keywordFilter) params.append('keywordFilter', keywordFilter);
    if (options.characterId) params.append('characterId', options.characterId);
    if (options.userId) params.append('userId', options.userId);
    if (options.limit) params.append('limit', options.limit.toString());
    if (options.minImportance) params.append('minImportance', options.minImportance.toString());
    
    const response = await fetch(`${this.baseUrl}/hybrid-search?${params.toString()}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error(`Failed to perform hybrid search: ${response.statusText}`);
    }
    
    return response.json();
  }
  
  /**
   * Get statistics about the context memory
   */
  async getMemoryStats(characterId?: string, userId?: string): Promise<any> {
    const params = new URLSearchParams();
    if (characterId) params.append('characterId', characterId);
    if (userId) params.append('userId', userId);
    
    const response = await fetch(`${this.baseUrl}/stats?${params.toString()}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error(`Failed to get memory stats: ${response.statusText}`);
    }
    
    return response.json();
  }
  
  /**
   * Save the current context session
   */
  async saveSession(sessionId: string, messages: Message[]): Promise<boolean> {
    const response = await fetch(`${this.baseUrl}/session/${sessionId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ messages }),
    });
    
    return response.ok;
  }
  
  /**
   * Load a context session
   */
  async loadSession(sessionId: string): Promise<ContextSession | null> {
    const response = await fetch(`${this.baseUrl}/session/${sessionId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      if (response.status === 404) return null;
      throw new Error(`Failed to load session: ${response.statusText}`);
    }
    
    return response.json();
  }
  
  /**
   * Delete a specific memory entry
   */
  async deleteMemory(memoryId: string): Promise<boolean> {
    const response = await fetch(`${this.baseUrl}/memory/${memoryId}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    return response.ok;
  }
  
  /**
   * Update the importance score of a memory
   */
  async updateImportanceScore(memoryId: string, newScore: number): Promise<boolean> {
    const response = await fetch(`${this.baseUrl}/memory/${memoryId}/importance`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ importanceScore: newScore }),
    });
    
    return response.ok;
  }
}

// Create a singleton instance
const contextAPI = new ContextAPI();

export { ContextAPI, contextAPI };
export type { Message, ContextSession, SearchResults, CompressionOptions, SearchOptions };