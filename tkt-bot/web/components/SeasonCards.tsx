"use client";

import styles from "./SeasonCards.module.css";

// Bốn thẻ câu hỏi theo mùa (REQ-09), nội dung từ mockup đã duyệt
const CARDS = [
  { k: "Mùa tuyển sinh", t: "Điểm chuẩn 2025 ba chuyên ngành", q: "Điểm chuẩn ngành Toán kinh tế 2025?" },
  { k: "Chi phí", t: "Học phí 2025-2026", q: "Học phí năm nhất bao nhiêu?" },
  { k: "Đào tạo", t: "Ba chuyên ngành và mã tuyển sinh", q: "Ngành có những chuyên ngành nào?" },
  { k: "Liên hệ", t: "Văn phòng A.205BIS", q: "Liên hệ văn phòng Khoa?" },
];

export default function SeasonCards({ onPick }: { onPick: (q: string) => void }) {
  return (
    <div className={styles.cards}>
      {CARDS.map((c) => (
        <button key={c.k} className={styles.card} onClick={() => onPick(c.q)}>
          <span className={styles.k}>{c.k}</span>
          <div className={styles.t}>{c.t}</div>
        </button>
      ))}
    </div>
  );
}
