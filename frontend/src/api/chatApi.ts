import type { ChatMode, ChatResponse, DocumentItem } from "../types/chat";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, options);

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const data = await response.json();
      // FastAPI validation 오류는 detail이 배열이므로 문자열일 때만 그대로 사용한다.
      if (typeof data.detail === "string") message = data.detail;
    } catch {
      // JSON이 아닌 오류 응답도 있으므로 HTTP 상태 기반 기본 메시지를 유지한다.
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export const chatApi = {
  uploadDocument(file: File) {
    // multipart 경계값은 브라우저가 설정해야 하므로 Content-Type을 직접 지정하지 않는다.
    const body = new FormData();
    body.append("file", file);
    return request<DocumentItem>("/api/documents", { method: "POST", body });
  },

  getDocuments() {
    return request<DocumentItem[]>("/api/documents");
  },

  deleteDocument(documentId: string) {
    return request<void>(`/api/documents/${documentId}`, { method: "DELETE" });
  },

  chat(question: string, mode: ChatMode) {
    return request<ChatResponse>("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, mode }),
    });
  },
};
