"use client";

import { useEffect, useRef, useState } from "react";
import type { Answer, ChatMessage, Citation, ResponseMode } from "@/lib/types";
import { streamChat, fetchClaimsCount } from "@/lib/api";
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
  const [responseMode, setResponseMode] = useState<ResponseMode>("mock");
  const [sheetCitation, setSheetCitation] = useState<Citation | null>(null);
  const [claims, setClaims] = useState<number | null>(null);
  const chatRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  // Số dữ kiện đọc từ /health, không hardcode (A3). Lỗi thì ẩn số.
  useEffect(() => {
    fetchClaimsCount().then(setClaims).catch(() => {});
  }, []);

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

    const controller = new AbortController();
    abortRef.current = controller;
    await streamChat(
      q,
      responseMode,
      {
        onPartial: (text) => patch({ text }),
        onAnswer: (answer: Answer) =>
          patch({ text: answer.answer_markdown, answer, pending: false }),
        onError: (err) =>
          patch({
            text: err,
            pending: false,
            answer: { answer_markdown: err, status: "null", citations: [], followups: [] },
          }),
      },
      controller.signal,
    );
    // dừng giữa chừng cũng phải tắt con trỏ, giữ nguyên phần đã stream
    patch({ pending: false });
    abortRef.current = null;
    setBusy(false);
  };

  const stop = () => abortRef.current?.abort();

  return (
    <div
      className={`${styles.phone} ${sheetCitation !== null ? styles.panelOpen : ""}`}
    >
      <header className={styles.header}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          className={styles.logo}
          src="/Logo-DH-Kinh-Te-Luat-UEL.webp"
          alt="Logo Trường Đại học Kinh tế - Luật, ĐHQG-HCM"
        />
        <div className={styles.wordmark}>
          <div className={styles.over}>Trường Đại học Kinh tế - Luật · ĐHQG-HCM</div>
          <div className={styles.name}>Khoa Toán Kinh tế</div>
        </div>
        <div className={styles.controls}>
          <ModeToggle
            value={responseMode}
            onChange={setResponseMode}
            disabled={busy}
          />
          <div className={styles.verified}>
            <span className={styles.vdot} />
            {claims !== null ? `${claims} dữ kiện kiểm chứng` : "Dữ kiện kiểm chứng"}
          </div>
        </div>
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
        {messages.map((msg, i) => (
          <MessageBubble
            key={msg.id}
            msg={msg}
            question={
              i > 0 && messages[i - 1].role === "user" ? messages[i - 1].text : ""
            }
            onOpenCitation={setSheetCitation}
            onPickFollowup={send}
          />
        ))}
      </main>

      <div className={styles.disclaimer}>
        Thông tin do AI tổng hợp từ nguồn công khai, có dẫn nguồn từng câu. Quyết định
        quan trọng xin xác nhận với văn phòng Khoa.
      </div>

      <InputBar onSend={send} disabled={busy} onStop={stop} />

      <EvidenceSheet citation={sheetCitation} onClose={() => setSheetCitation(null)} />
    </div>
  );
}
