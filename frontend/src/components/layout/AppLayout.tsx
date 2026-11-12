import { useEffect } from "react";

import { ChatWindow } from "../chat/ChatWindow";
import { Sidebar } from "./Sidebar";
import { useChatStore } from "../../stores/chatStore";

export function AppLayout() {
  const fetchDocuments = useChatStore((state) => state.fetchDocuments);

  useEffect(() => {
    // 앱 셸이 처음 마운트될 때 사이드바 문서 목록을 한 번 불러온다.
    void fetchDocuments();
  }, [fetchDocuments]);

  return (
    <div className="flex h-dvh flex-col overflow-hidden bg-[#212121] text-zinc-100 md:flex-row">
      <Sidebar />
      <ChatWindow />
    </div>
  );
}
