import { Sparkles } from "lucide-react";

export function EmptyChat() {
  return (
    <div className="flex h-full items-center justify-center px-4">
      <div className="w-full max-w-xl text-center">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-white/10">
          <Sparkles className="h-5 w-5 text-zinc-200" />
        </div>
        <h1 className="mt-5 text-2xl font-semibold text-zinc-100">Ask your documents</h1>
        <p className="mt-3 text-sm leading-6 text-zinc-400">
          Upload PDF, TXT or Markdown files, then ask a question. Answers cite the source chunks they rely on.
        </p>
      </div>
    </div>
  );
}
