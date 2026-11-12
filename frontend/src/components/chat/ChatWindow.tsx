import { AlertCircle } from "lucide-react";

import { ChatInput } from "./ChatInput";
import { EmptyChat } from "./EmptyChat";
import { MessageList } from "./MessageList";
import { useChatStore } from "../../stores/chatStore";
import type { ChatMode } from "../../types/chat";
import { cn } from "../../utils/cn";

const MODES: { value: ChatMode; label: string; hint: string }[] = [
  { value: "rag", label: "RAG", hint: "Always retrieve, then answer (deterministic 2-step)" },
  { value: "agent", label: "Agent", hint: "Model decides when to call document tools" },
];

export function ChatWindow() {
  const messages = useChatStore((state) => state.messages);
  const error = useChatStore((state) => state.error);
  const mode = useChatStore((state) => state.mode);
  const setMode = useChatStore((state) => state.setMode);
  const isLoading = useChatStore((state) => state.isLoading);

  return (
    <main className="flex min-h-0 min-w-0 flex-1 flex-col bg-[#212121]">
      <header className="flex h-14 shrink-0 items-center justify-between border-b border-white/10 px-4">
        <span className="text-sm font-medium text-zinc-300">rag-langchain</span>
        <div role="radiogroup" aria-label="Chat mode" className="flex rounded-lg border border-white/10 p-0.5">
          {MODES.map((item) => (
            <button
              key={item.value}
              type="button"
              role="radio"
              aria-checked={mode === item.value}
              title={item.hint}
              disabled={isLoading}
              onClick={() => setMode(item.value)}
              className={cn(
                "rounded-md px-3 py-1 text-sm transition",
                mode === item.value ? "bg-zinc-100 text-zinc-950" : "text-zinc-400 hover:text-zinc-100",
              )}
            >
              {item.label}
            </button>
          ))}
        </div>
      </header>

      {error && (
        <div
          role="alert"
          className="mx-auto mt-3 flex w-[min(760px,calc(100%-24px))] items-center gap-2 rounded-lg border border-red-400/30 bg-red-950/30 px-3 py-2 text-sm text-red-100"
        >
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span className="min-w-0">{error}</span>
        </div>
      )}

      <div className="min-h-0 flex-1">{messages.length > 0 ? <MessageList /> : <EmptyChat />}</div>

      <ChatInput />
    </main>
  );
}
