/**
 * Context Store for managing dialog context in the frontend
 * Implements reactive state management for context with Vue 3
 */

import { ref, reactive, computed, ComputedRef } from 'vue';
import { Message, ContextSession, ContextStoreState } from './types';

// Define the store state
const state: ContextStoreState = reactive({
  messages: [],
  currentSessionId: null,
  compressedMessages: [],
  selectedMessages: new Set<string>(),
  memoryStats: {
    totalMemories: 0,
    averageImportance: 0,
    timeRange: { min: null, max: null }
  },
  isCompressing: false,
  searchResults: [],
  isSearching: false
});

// Actions
const addMessage = (message: Message): void => {
  state.messages.push(message);
};

const addMessages = (messages: Message[]): void => {
  state.messages.push(...messages);
};

const updateMessage = (id: string, updates: Partial<Message>): void => {
  const index = state.messages.findIndex(msg => msg.id === id);
  if (index !== -1) {
    Object.assign(state.messages[index], updates);
  }
};

const removeMessage = (id: string): void => {
  const index = state.messages.findIndex(msg => msg.id === id);
  if (index !== -1) {
    state.messages.splice(index, 1);
  }
};

const compressContext = async (compressionRatio: number = 0.5): Promise<void> => {
  state.isCompressing = true;
  try {
    // Simulate API call to backend compression
    const response = await fetch('/api/context/compress', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: state.messages,
        compressionRatio
      })
    });
    
    if (response.ok) {
      const result = await response.json();
      state.compressedMessages = result.compressedMessages;
    }
  } catch (error) {
    console.error('Error compressing context:', error);
  } finally {
    state.isCompressing = false;
  }
};

const searchMemory = async (query: string, characterId?: string): Promise<void> => {
  state.isSearching = true;
  try {
    const params = new URLSearchParams({ query });
    if (characterId) params.append('characterId', characterId);
    
    const response = await fetch(`/api/context/search?${params.toString()}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });
    
    if (response.ok) {
      const result = await response.json();
      state.searchResults = result.results;
    }
  } catch (error) {
    console.error('Error searching memory:', error);
  } finally {
    state.isSearching = false;
  }
};

const toggleMessageSelection = (id: string): void => {
  if (state.selectedMessages.has(id)) {
    state.selectedMessages.delete(id);
  } else {
    state.selectedMessages.add(id);
  }
};

const clearSelection = (): void => {
  state.selectedMessages.clear();
};

const startNewSession = (sessionId: string): void => {
  state.currentSessionId = sessionId;
  state.messages = [];
  state.compressedMessages = [];
  state.selectedMessages.clear();
};

const loadSession = async (sessionId: string): Promise<void> => {
  try {
    const response = await fetch(`/api/context/session/${sessionId}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });
    
    if (response.ok) {
      const sessionData = await response.json();
      state.currentSessionId = sessionId;
      state.messages = sessionData.messages || [];
      state.compressedMessages = [];
      state.selectedMessages.clear();
    }
  } catch (error) {
    console.error('Error loading session:', error);
  }
};

const saveSession = async (sessionId?: string): Promise<void> => {
  const id = sessionId || state.currentSessionId;
  if (!id) return;
  
  try {
    await fetch(`/api/context/session/${id}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: state.messages
      })
    });
  } catch (error) {
    console.error('Error saving session:', error);
  }
};

// Computed properties
const messageCount = computed(() => state.messages.length);
const selectedCount = computed(() => state.selectedMessages.size);
const hasMessages = computed(() => state.messages.length > 0);

// Initialize the store
export const useContextStore = () => ({
  // State
  state,
  
  // Getters
  messageCount,
  selectedCount,
  hasMessages,
  
  // Actions
  addMessage,
  addMessages,
  updateMessage,
  removeMessage,
  compressContext,
  searchMemory,
  toggleMessageSelection,
  clearSelection,
  startNewSession,
  loadSession,
  saveSession
});

// Export types
export type { ContextStoreState };