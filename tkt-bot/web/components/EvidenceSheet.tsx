"use client";

import React, { useEffect, useRef } from "react";
import type { Citation } from "@/lib/types";
import styles from "./EvidenceSheet.module.css";

function highlightNumbers(text: string): React.ReactNode[] {
  return text
    .split(/(\d+(?:[.,]\d+)*)/g)
    .map((p, i) => (/^\d/.test(p) ? <mark key={i}>{p}</mark> : p));
}

function fmtFetchedAt(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const pad = (n: number) => String(n).padStart(2, "0");
  return `Chụp lúc ${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())} · ${pad(d.getUTCDate())}/${pad(d.getUTCMonth() + 1)}/${d.getUTCFullYear()}`;
}

export default function EvidenceSheet({
  citation,
  onClose,
}: {
  citation: Citation | null;
  onClose: () => void;
}) {
  const open = citation !== null;
  const sheetRef = useRef<HTMLElement>(null);
  const returnFocusRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!open) return;
    returnFocusRef.current = document.activeElement as HTMLElement | null;
    sheetRef.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("keydown", onKey);
      returnFocusRef.current?.focus();
    };
  }, [open, onClose]);

  return (
    <>
      <div
        className={`${styles.backdrop} ${open ? styles.show : ""}`}
        onClick={onClose}
        aria-hidden="true"
      />
      <section
        ref={sheetRef}
        tabIndex={-1}
        className={`${styles.sheet} ${open ? styles.open : ""}`}
        aria-label="Chi tiết nguồn dẫn"
        aria-hidden={!open}
      >
        {citation && (
          <>
            <button
              className={styles.close}
              onClick={onClose}
              aria-label="Đóng chi tiết nguồn dẫn"
            >
              ×
            </button>
            <div className={styles.grab} />
            <div className={styles.head}>
              <span className={`${styles.tier} ${styles[`tier${citation.tier}`]}`}>
                {citation.tier}
              </span>
              <div>
                <div className={styles.src}>{citation.source}</div>
                <div className={styles.meta}>{fmtFetchedAt(citation.fetched_at)}</div>
              </div>
            </div>
            <div className={styles.evLabel}>Đoạn gốc nguyên văn (evidence_span)</div>
            <p className={styles.evidence}>{highlightNumbers(citation.evidence_span)}</p>
            <div className={styles.rows}>
              <div className={styles.row}>
                <span>Mã dẫn nguồn</span>
                <span>{citation.claim_id}</span>
              </div>
              <div className={styles.row}>
                <span>URL nguồn</span>
                <span>{citation.url}</span>
              </div>
            </div>
            <p className={styles.note}>
              Tier A: nguồn chính chủ (site Khoa, Trường). Tier B: báo chí. Tier C:
              trang tổng hợp. Mọi giá trị đều dẫn được về bản chụp gốc trong kho
              snapshot.
            </p>
          </>
        )}
      </section>
    </>
  );
}
