import { useRef } from "react";
import { FileText, Loader2, Trash2, Upload } from "lucide-react";

import { useChatStore } from "../../stores/chatStore";

const ACCEPT = ".pdf,.txt,.md,.markdown";

export function Sidebar() {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const documents = useChatStore((state) => state.documents);
  const isUploading = useChatStore((state) => state.isUploading);
  const deletingId = useChatStore((state) => state.deletingId);
  const documentError = useChatStore((state) => state.documentError);
  const uploadDocuments = useChatStore((state) => state.uploadDocuments);
  const deleteDocument = useChatStore((state) => state.deleteDocument);

  return (
    <aside className="flex shrink-0 flex-col border-white/10 bg-[#171717] max-md:max-h-[40dvh] max-md:border-b md:h-dvh md:w-[280px] md:border-r">
      <div className="flex h-14 shrink-0 items-center justify-between px-4">
        <span className="text-sm font-semibold text-zinc-200">Documents</span>
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          disabled={isUploading}
          className="inline-flex h-9 items-center gap-2 rounded-lg border border-white/10 bg-white/[0.04] px-3 text-sm text-zinc-100 transition hover:bg-white/[0.08] disabled:opacity-50"
        >
          {isUploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
          {isUploading ? "Uploading" : "Upload"}
        </button>
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT}
          multiple
          hidden
          onChange={(event) => {
            const files = Array.from(event.target.files ?? []);
            // 같은 파일을 다시 선택해도 change 이벤트가 발생하도록 값을 비운다.
            event.target.value = "";
            if (files.length) void uploadDocuments(files);
          }}
        />
      </div>

      {documentError && (
        <p className="mx-3 mb-2 whitespace-pre-wrap rounded-lg border border-red-400/30 bg-red-950/30 px-3 py-2 text-xs text-red-100">
          {documentError}
        </p>
      )}

      <ul className="min-h-0 flex-1 space-y-1 overflow-y-auto px-2 pb-3">
        {documents.length === 0 && (
          <li className="px-2 py-3 text-xs text-zinc-500">No documents yet. Upload PDF, TXT or Markdown.</li>
        )}
        {documents.map((doc) => (
          <li key={doc.id} className="group flex items-center gap-2 rounded-lg px-2 py-2 hover:bg-white/[0.06]">
            <FileText className="h-4 w-4 shrink-0 text-zinc-400" />
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm text-zinc-100" title={doc.filename}>
                {doc.filename}
              </p>
              <p className="text-xs text-zinc-500">
                {doc.chunk_count} chunks · {(doc.size_bytes / 1024).toFixed(1)} KB
              </p>
            </div>
            <button
              type="button"
              title="Delete document"
              aria-label={`Delete ${doc.filename}`}
              disabled={deletingId === doc.id}
              onClick={() => {
                if (window.confirm(`Delete "${doc.filename}"?`)) void deleteDocument(doc.id);
              }}
              className="rounded p-1 text-zinc-500 hover:bg-white/10 hover:text-red-300 disabled:opacity-50"
            >
              {deletingId === doc.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
            </button>
          </li>
        ))}
      </ul>
    </aside>
  );
}
