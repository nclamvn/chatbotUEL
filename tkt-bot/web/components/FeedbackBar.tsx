"use client";

import { useState } from "react";
import { postFeedback } from "@/lib/api";
import styles from "./FeedbackBar.module.css";

// TIP-13: thu phản hồi sau mỗi câu trả lời. Thumbs up gửi ngay; thumbs down mở
// ô góp ý một dòng tùy chọn. Feedback không bao giờ chặn UX (lỗi thì im lặng).
export default function FeedbackBar({ question }: { question: string }) {
  const [done, setDone] = useState(false);
  const [askComment, setAskComment] = useState(false);
  const [comment, setComment] = useState("");

  const up = () => {
    postFeedback(question, "up");
    setDone(true);
  };
  const submitDown = () => {
    postFeedback(question, "down", comment.trim() || undefined);
    setDone(true);
  };

  if (done) return <div className={styles.thanks}>Cảm ơn góp ý của bạn.</div>;

  return (
    <div className={styles.bar}>
      {!askComment ? (
        <>
          <span className={styles.label}>Câu trả lời có hữu ích không?</span>
          <button className={styles.btn} onClick={up} aria-label="Hữu ích">
            Có
          </button>
          <button
            className={styles.btn}
            onClick={() => setAskComment(true)}
            aria-label="Chưa đúng"
          >
            Chưa
          </button>
        </>
      ) : (
        <>
          <input
            className={styles.input}
            value={comment}
            placeholder="Góp ý một dòng (tùy chọn)…"
            aria-label="Góp ý"
            onChange={(e) => setComment(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") submitDown();
            }}
          />
          <button className={styles.send} onClick={submitDown}>
            Gửi
          </button>
        </>
      )}
    </div>
  );
}
