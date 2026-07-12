"use client";

import { useEffect, useRef, useState } from "react";
import type { Answer, ChatMessage, Citation } from "@/lib/types";
import { streamChat } from "@/lib/api";
import EvidenceSheet from "./EvidenceSheet";
import InputBar from "./InputBar";
import MessageBubble from "./MessageBubble";
import ModeToggle from "./ModeToggle";
import SeasonCards from "./SeasonCards";
import styles from "./ChatSurface.module.css";

let nextId = 0;
const mid = () => `m${nextId++}`;

export default function ChatSurface() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [busy, setBusy] = useState(false);
  const [sheetCitation, setSheetCitation] = useState<Citation | null>(null);
  const chatRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatRef.current?.scrollTo({ top: chatRef.current.scrollHeight });
  }, [messages]);

  const send = async (q: string) => {
    if (busy) return;
    setBusy(true);
    const botId = mid();
    setMessages((m) => [
      ...m,
      { id: mid(), role: "user", text: q },
      { id: botId, role: "bot", text: "", pending: true },
    ]);

    const patch = (p: Partial<ChatMessage>) =>
      setMessages((m) => m.map((x) => (x.id === botId ? { ...x, ...p } : x)));

    await streamChat(q, {
      onPartial: (text) => patch({ text }),
      onAnswer: (answer: Answer) =>
        patch({ text: answer.answer_markdown, answer, pending: false }),
      onError: (err) =>
        patch({
          text: err,
          pending: false,
          answer: { answer_markdown: err, status: "null", citations: [], followups: [] },
        }),
    });
    setBusy(false);
  };

  return (
    <div
      className={`${styles.phone} ${sheetCitation !== null ? styles.panelOpen : ""}`}
    >
      <header className={styles.header}>
        <div className={styles.mark}>∑</div>
        <div className={styles.hTitle}>
          <div className={styles.eyebrow}>UEL · Cổng hỏi đáp</div>
          <h1>Khoa Toán Kinh tế</h1>
          <div className={styles.hStatus}>
            <span className={styles.dot} />
            Dữ liệu kiểm chứng · cập nhật 12/07/2026
          </div>
        </div>
        <ModeToggle />
      </header>

      <main className={styles.chat} ref={chatRef}>
        <span className={styles.day}>Hôm nay</span>
        {messages.length === 0 && (
          <div className={styles.welcome}>
            <p>
              Chào bạn. Mình trả lời về <b>tuyển sinh, đào tạo, nghiên cứu và học vụ</b>{" "}
              của Khoa Toán Kinh tế. Mỗi con số đều kèm dẫn nguồn, chạm vào nhãn nguồn
              để xem đoạn gốc.
            </p>
            <SeasonCards onPick={send} />
          </div>
        )}
        {messages.map((msg) => (
          <MessageBubble
            key={msg.id}
            msg={msg}
            onOpenCitation={setSheetCitation}
            onPickFollowup={send}
          />
        ))}
      </main>

      <div className={styles.disclaimer}>
        Thông tin do AI tổng hợp từ nguồn công khai, có dẫn nguồn từng câu. Quyết định
        quan trọng xin xác nhận với văn phòng Khoa.
      </div>

      <InputBar onSend={send} disabled={busy} />

      <EvidenceSheet citation={sheetCitation} onClose={() => setSheetCitation(null)} />
    </div>
  );
}
