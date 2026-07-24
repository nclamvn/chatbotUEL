"use client";

import type { ResponseMode } from "@/lib/types";
import styles from "./ModeToggle.module.css";

export default function ModeToggle({
  value,
  onChange,
  disabled = false,
}: {
  value: ResponseMode;
  onChange: (mode: ResponseMode) => void;
  disabled?: boolean;
}) {
  return (
    <div
      className={styles.mode}
      role="group"
      aria-label="Chọn chế độ trả lời"
      title={
        value === "mock"
          ? "Demo ổn định, không gọi API"
          : "Gọi OpenAI trực tiếp, tự động dự phòng qua Claude"
      }
    >
      <button
        type="button"
        className={value === "mock" ? styles.active : ""}
        aria-pressed={value === "mock"}
        disabled={disabled}
        onClick={() => onChange("mock")}
      >
        Demo
      </button>
      <button
        type="button"
        className={value === "api" ? styles.activeApi : ""}
        aria-pressed={value === "api"}
        disabled={disabled}
        onClick={() => onChange("api")}
      >
        <span className={styles.liveDot} aria-hidden="true" />
        AI trực tiếp
      </button>
    </div>
  );
}
