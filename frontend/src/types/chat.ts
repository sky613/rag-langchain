export type ChatRole = "user" | "assistant";
export type ChatMode = "rag" | "agent";

// 컴포넌트, Zustand 스토어, chatApi가 함께 사용하는 백엔드 응답 타입이다.
export type DocumentItem = {
  id: string;
  filename: string;
  file_type: string;
  size_bytes: number;
  chunk_count: number;
  created_at: string;
};

export type Source = {
  chunk_id: string;
  document_id: string;
  filename: string;
  page: number | null;
  chunk_index: number;
  snippet: string;
};

export type TokenUsage = {
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
};

export type ChatResponse = {
  answer: string;
  mode: ChatMode;
  sources: Source[];
  cited_chunk_ids: string[];
  tool_calls: string[];
  usage: TokenUsage;
  latency_ms: number;
  estimated_cost_usd: number;
};

// 대화는 서버에 저장하지 않으므로 화면 표시용 메시지만 클라이언트에서 관리한다.
export type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
  response?: ChatResponse;
};
