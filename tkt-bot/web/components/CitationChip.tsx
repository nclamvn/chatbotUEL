"use client";

import type { Citation } from "@/lib/types";
import TierBadge from "./TierBadge";
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
      <TierBadge tier={citation.tier} size="sm" />
      {citation.source}
    </button>
  );
}
