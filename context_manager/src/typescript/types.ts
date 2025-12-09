/**
 * Type definitions for the context management system
 */

export interface Message {
  id: string;
  text: string;
  role: 'user' | 'assistant' | 'system';
  timestamp: string;
  importanceScore?: number;
  characterId?: string;
  userId?: string;
  metadata?: Record<string, any>;
  source?: string; // 'memory', 'current', etc.
}

export interface ContextSession {
  id: string;
  messages: Message[];
  createdAt: string;
  updatedAt: string;
  characterId?: string;
  userId?: string;
}

export interface MemoryStats {
  totalMemories: number;
  averageImportance: number;
  timeRange: {
    min: string | null;
    max: string | null;
  };
  characterId?: string;
  userId?: string;
}

export interface SearchResults {
  query: string;
  results: Message[];
  executionTimeMs: number;
}

export interface ContextStoreState {
  messages: Message[];
  currentSessionId: string | null;
  compressedMessages: Message[];
  selectedMessages: Set<string>;
  memoryStats: MemoryStats;
  isCompressing: boolean;
  searchResults: SearchResults[];
  isSearching: boolean;
}

export interface CompressionOptions {
  targetLength?: number;
  compressionRatio?: number;
  maxContextSize?: number;
}

export interface SearchOptions {
  characterId?: string;
  userId?: string;
  limit?: number;
  minImportance?: number;
  keywordFilter?: string;
}