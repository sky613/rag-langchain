import ReactMarkdown from "react-markdown";
import rehypeHighlight from "rehype-highlight";

import type { ChatMessage, ChatResponse } from "../../types/chat";
import { cn } from "../../utils/cn";

export function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  return (
    <article className={cn("flex w-full", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[88%] rounded-2xl px-4 py-3 text-[15px] leading-7 shadow-sm",
          isUser
            ? "bg-[#2f2f2f] text-zinc-50"
            : "bg-transparent px-0 text-zinc-100 shadow-none",
        )}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap break-words">{message.content}</p>
        ) : (
          // LLM 답변에는 Markdown과 코드 블록이 포함될 수 있어 렌더러를 분리한다.
          <ReactMarkdown
            rehypePlugins={[rehypeHighlight]}
            components={{
              pre({ children }) {
                return (
                  <pre className="my-4 overflow-x-auto rounded-lg border border-white/10 bg-[#0d0d0d] p-4 text-sm leading-6">
                    {children}
                  </pre>
                );
              },
              code({ className, children }) {
                return (
                  <code className={cn("rounded bg-white/10 px-1.5 py-0.5 text-sm", className)}>
                    {children}
                  </code>
                );
              },
              p({ children }) {
                return <p className="mb-3 last:mb-0">{children}</p>;
              },
              ul({ children }) {
                return <ul className="mb-3 list-disc space-y-1 pl-5">{children}</ul>;
              },
              ol({ children }) {
                return <ol className="mb-3 list-decimal space-y-1 pl-5">{children}</ol>;
              },
              a({ children, href }) {
                return (
                  <a
                    href={href}
                    target="_blank"
                    rel="noreferrer"
                    className="text-blue-300 underline underline-offset-4 hover:text-blue-200"
                  >
                    {children}
                  </a>
                );
              },
            }}
          >
            {message.content}
          </ReactMarkdown>
        )}
        {message.response && <ResponseDetails response={message.response} />}
      </div>
    </article>
  );
}

function ResponseDetails({ response }: { response: ChatResponse }) {
  const cited = new Set(response.cited_chunk_ids);

  return (
    <div className="mt-3 space-y-2 text-xs text-zinc-400">
      {response.sources.length > 0 && (
        <details className="rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2">
          <summary className="cursor-pointer select-none text-zinc-300">
            Sources ({response.cited_chunk_ids.length} cited / {response.sources.length} retrieved)
          </summary>
          <ul className="mt-2 space-y-2">
            {response.sources.map((source) => (
              <li key={source.chunk_id} className="rounded-md bg-black/20 p-2">
                <p className="flex flex-wrap items-center gap-x-2 text-zinc-300">
                  <span className="font-medium">{source.filename}</span>
                  {source.page !== null && <span>p.{source.page}</span>}
                  <code className="text-[11px] text-zinc-500">{source.chunk_id}</code>
                  {cited.has(source.chunk_id) && (
                    <span className="rounded bg-emerald-500/20 px-1.5 text-emerald-300">cited</span>
                  )}
                </p>
                <p className="mt-1 line-clamp-3 whitespace-pre-wrap text-zinc-400">{source.snippet}</p>
              </li>
            ))}
          </ul>
        </details>
      )}
      <p>
        {response.mode.toUpperCase()}
        {response.tool_calls.length > 0 && ` · tools: ${response.tool_calls.join(", ")}`} · {response.latency_ms} ms ·{" "}
        {response.usage.input_tokens}/{response.usage.output_tokens} tokens (in/out) · $
        {response.estimated_cost_usd.toFixed(6)}
      </p>
    </div>
  );
}
