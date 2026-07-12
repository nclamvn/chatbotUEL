"use client";

import type { Citation } from "@/lib/types";
import styles from "./CitationChip.module.css";

export default function CitationChip({
  citation,
  onOpen,
}: {
  citation: Citation;
  onOpen: (c: Citation) => void;
}) {
  return (
    <button className={styles.chip} onClick={() => onOpen(citation)}>
      <span className={`${styles.tier} ${styles[`tier${citation.tier}`]}`}>
        {citation.tier}
      </span>
      {citation.source}
    </button>
  );
}
