import type { Citation } from "@/lib/types";
import { cleanEvidence } from "@/lib/cleanEvidence";
import styles from "./DisputedBlock.module.css";

export default function DisputedBlock({ citations }: { citations: Citation[] }) {
  return (
    <div className={styles.disputed}>
      <span className={styles.bt}>⚠ Nguồn chưa thống nhất</span>
      {citations.map((c) => {
        const ev = cleanEvidence(c.evidence_span); // gỡ HTML thô trước, rồi mới cắt 90 ký tự
        return (
        <div key={c.claim_id} className={styles.v}>
          <span>{ev.length > 90 ? `${ev.slice(0, 90)}…` : ev}</span>
          <span>
            {c.source} · {c.tier}
          </span>
        </div>
        );
      })}
      Các nguồn trên ghi khác nhau. Mình giữ nguyên mọi phiên bản, bạn nên xác nhận
      qua văn phòng Khoa.
    </div>
  );
}
