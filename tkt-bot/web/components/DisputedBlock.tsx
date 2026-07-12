import type { Citation } from "@/lib/types";
import styles from "./DisputedBlock.module.css";

export default function DisputedBlock({ citations }: { citations: Citation[] }) {
  return (
    <div className={styles.disputed}>
      <span className={styles.bt}>⚠ Nguồn chưa thống nhất</span>
      {citations.map((c) => (
        <div key={c.claim_id} className={styles.v}>
          <span>{c.evidence_span.length > 90 ? `${c.evidence_span.slice(0, 90)}…` : c.evidence_span}</span>
          <span>
            {c.source} · {c.tier}
          </span>
        </div>
      ))}
      Các nguồn trên ghi khác nhau. Mình giữ nguyên mọi phiên bản, bạn nên xác nhận
      qua văn phòng Khoa.
    </div>
  );
}
