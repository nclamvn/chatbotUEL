"use client";

import type { ChatMessage, Citation } from "@/lib/types";
import { renderMarkdown } from "@/lib/markdown";
import CitationChip from "./CitationChip";
import DisputedBlock from "./DisputedBlock";
import FeedbackBar from "./FeedbackBar";
import NullBlock from "./NullBlock";
import styles from "./MessageBubble.module.css";

export default function MessageBubble({
  msg,
  question,
  onOpenCitation,
  onPickFollowup,
}: {
  msg: ChatMessage;
  question: string;
  onOpenCitation: (c: Citation) => void;
  onPickFollowup: (q: string) => void;
}) {
  if (msg.role === "user") {
    return (
      <div className={`${styles.msg} ${styles.user}`}>
        <div className={styles.bubble}>{msg.text}</div>
      </div>
    );
  }

  const a = msg.answer;
  const status = a?.status;
  return (
    <div className={`${styles.msg} ${styles.bot}`}>
      <div className={styles.bubble}>
        {status === "null" || status === "oos" ? (
          <NullBlock kind={status}>{renderMarkdown(msg.text)}</NullBlock>
        ) : (
          renderMarkdown(msg.text)
        )}
        {msg.pending && <span className={styles.cursor}>▍</span>}
        {status === "disputed" && a && <DisputedBlock citations={a.citations} />}
      </div>
      {a && a.citations.length > 0 && (
        <div className={styles.chips}>
          {a.citations.map((c) => (
            <CitationChip key={c.claim_id} citation={c} onOpen={onOpenCitation} />
          ))}
        </div>
      )}
      {a && a.followups.length > 0 && (
        <div className={styles.fu}>
          {a.followups.slice(0, 3).map((f) => (
            <button key={f} onClick={() => onPickFollowup(f)}>
              {f}
            </button>
          ))}
        </div>
      )}
      {a && !msg.pending && question && <FeedbackBar question={question} />}
    </div>
  );
}
