import { create } from "zustand";

import { chatApi } from "../api/chatApi";
import type { ChatMessage, ChatMode, DocumentItem } from "../types/chat";

type ChatState = {
  documents: DocumentItem[];
  isUploading: boolean;
  deletingId: string | null;
  documentError: string | null;
  messages: ChatMessage[];
  mode: ChatMode;
  isLoading: boolean;
  error: string | null;
  fetchDocuments: () => Promise<void>;
  uploadDocuments: (files: File[]) => Promise<void>;
  deleteDocument: (documentId: string) => Promise<void>;
  setMode: (mode: ChatMode) => void;
  sendMessage: (content: string) => Promise<void>;
};

const toMessage = (error: unknown) => (error instanceof Error ? error.message : "Unexpected error");

export const useChatStore = create<ChatState>((set, get) => ({
  documents: [],
  isUploading: false,
  deletingId: null,
  documentError: null,
  messages: [],
  mode: "rag",
  isLoading: false,
  error: null,

  async fetchDocuments() {
    try {
      set({ documents: await chatApi.getDocuments(), documentError: null });
    } catch (error) {
      set({ documentError: toMessage(error) });
    }
  },

  async uploadDocuments(files) {
    set({ isUploading: true, documentError: null });
    const errors: string[] = [];
    // 파일별 결과를 독립적으로 처리해 하나가 실패(중복 등)해도 나머지는 업로드한다.
    for (const file of files) {
      try {
        await chatApi.uploadDocument(file);
      } catch (error) {
        errors.push(`${file.name}: ${toMessage(error)}`);
      }
    }
    set({ isUploading: false, documentError: errors.length ? errors.join("\n") : null });
    await get().fetchDocuments();
  },

  async deleteDocument(documentId) {
    set({ deletingId: documentId, documentError: null });
    try {
      await chatApi.deleteDocument(documentId);
      set((state) => ({ documents: state.documents.filter((doc) => doc.id !== documentId) }));
    } catch (error) {
      set({ documentError: toMessage(error) });
    } finally {
      set({ deletingId: null });
    }
  },

  setMode(mode) {
    set({ mode });
  },

  async sendMessage(content) {
    const question = content.trim();
    if (!question || get().isLoading) return;

    const userMessage: ChatMessage = { id: crypto.randomUUID(), role: "user", content: question };
    set((state) => ({ messages: [...state.messages, userMessage], isLoading: true, error: null }));

    try {
      const response = await chatApi.chat(question, get().mode);
      const assistantMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: response.answer,
        response,
      };
      set((state) => ({ messages: [...state.messages, assistantMessage] }));
    } catch (error) {
      set({ error: toMessage(error) });
    } finally {
      set({ isLoading: false });
    }
  },
}));
