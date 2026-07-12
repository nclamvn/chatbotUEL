"use client";

import { useState } from "react";
import styles from "./InputBar.module.css";

export default function InputBar({
  onSend,
  disabled,
}: {
  onSend: (q: string) => void;
  disabled: boolean;
}) {
  const [value, setValue] = useState("");

  const submit = () => {
    const q = value.trim();
    if (!q || disabled) return;
    setValue("");
    onSend(q);
  };

  return (
    <div className={styles.inputbar}>
      <input
        type="text"
        value={value}
        placeholder="Hỏi về tuyển sinh, đào tạo, học vụ…"
        autoComplete="off"
        aria-label="Câu hỏi của bạn"
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") submit();
        }}
      />
      <button
        className={styles.send}
        onClick={submit}
        disabled={disabled}
        aria-label="Gửi câu hỏi"
      >
        ↑
      </button>
    </div>
  );
}
