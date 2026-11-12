import { useEffect, useRef } from "react";

import { MessageBubble } from "./MessageBubble";
import { useChatStore } from "../../stores/chatStore";

export function MessageList() {
  const messages = useChatStore((state) => state.messages);
  const isLoading = useChatStore((state) => state.isLoading);
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    // 새 메시지나 로딩 표시가 추가되면 최신 메시지가 보이도록 아래로 스크롤한다.
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages.length, isLoading]);

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto flex min-h-full w-full max-w-3xl flex-col gap-5 px-4 py-8">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        {isLoading && messages.length > 0 && (
          <div className="flex items-center gap-2 px-1 text-sm text-zinc-400">
            <span className="h-2 w-2 animate-pulse rounded-full bg-zinc-400" />
            <span>Generating response</span>
          </div>
        )}
        <div ref={endRef} />
      </div>
    </div>
  );
}

