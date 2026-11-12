import { useEffect, useRef, useState } from "react";
import { ArrowUp } from "lucide-react";

import { useChatStore } from "../../stores/chatStore";
import { cn } from "../../utils/cn";

export function ChatInput() {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const sendMessage = useChatStore((state) => state.sendMessage);
  const isLoading = useChatStore((state) => state.isLoading);
  const canSend = value.trim().length > 0 && !isLoading;

  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    // 높이를 매번 초기화해야 텍스트 삭제 시 textarea도 다시 줄어든다.
    textarea.style.height = "0px";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 180)}px`;
  }, [value]);

  const submit = () => {
    if (!canSend) return;

    // 입력창은 즉시 비우고, 낙관적 메시지와 스트리밍 처리는 스토어에 맡긴다.
    const message = value;
    setValue("");
    void sendMessage(message);
  };

  return (
    <div className="shrink-0 bg-gradient-to-t from-[#212121] via-[#212121] to-transparent px-3 pb-4 pt-3">
      <div className="mx-auto max-w-3xl">
        <div className="flex items-end gap-2 rounded-2xl border border-white/10 bg-[#2f2f2f] p-2 shadow-lg">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(event) => setValue(event.target.value)}
            onKeyDown={(event) => {
              // 일반적인 채팅 UX에 맞춰 Enter는 전송, Shift+Enter는 줄바꿈으로 처리한다.
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                submit();
              }
            }}
            rows={1}
            placeholder="Type a message"
            className="max-h-[180px] min-h-10 flex-1 resize-none bg-transparent px-2 py-2.5 text-[15px] leading-6 text-zinc-100 outline-none placeholder:text-zinc-500"
          />
          <button
            type="button"
            onClick={submit}
            disabled={!canSend}
            title="Send"
            className={cn(
              "flex h-10 w-10 shrink-0 items-center justify-center rounded-full transition",
              canSend
                ? "bg-zinc-100 text-zinc-950 hover:bg-white"
                : "bg-zinc-700 text-zinc-500",
            )}
          >
            <ArrowUp className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

