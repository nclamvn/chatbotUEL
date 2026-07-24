"use client";

import { useState } from "react";
import styles from "./InputBar.module.css";

// Một icon duy nhất, đổi màu theo currentColor (A3 InputBar v2).
function ArrowIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M5 12h14" />
      <path d="M13 6l6 6-6 6" />
    </svg>
  );
}

function StopIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <rect x="7" y="7" width="10" height="10" rx="1.5" />
    </svg>
  );
}

export default function InputBar({
  onSend,
  disabled,
  onStop,
}: {
  onSend: (q: string) => void;
  disabled: boolean;
  onStop?: () => void;
}) {
  const [value, setValue] = useState("");
  const canSend = value.trim().length > 0 && !disabled;

  const submit = () => {
    if (!canSend) return;
    const q = value.trim();
    setValue("");
    onSend(q);
  };

  return (
    <div className={styles.inputbar}>
      <div className={styles.box} aria-busy={disabled}>
        <input
          type="text"
          value={value}
          placeholder={
            disabled
              ? "Đang kiểm tra nguồn và soạn câu trả lời…"
              : "Hỏi về tuyển sinh, đào tạo, học vụ…"
          }
          autoComplete="off"
          aria-label="Câu hỏi của bạn"
          disabled={disabled}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") submit();
          }}
        />
        {disabled ? (
          // đang stream: ô vuông dừng, cùng kích thước cùng vị trí, không giật layout
          <button
            type="button"
            className={styles.go}
            onClick={onStop}
            aria-label="Dừng tạo câu trả lời"
          >
            <StopIcon />
          </button>
        ) : (
          <button
            type="button"
            className={styles.go}
            onClick={submit}
            disabled={!canSend}
            aria-label="Gửi câu hỏi"
          >
            <ArrowIcon />
          </button>
        )}
      </div>
    </div>
  );
}
