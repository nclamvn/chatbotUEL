import styles from "./NullBlock.module.css";

export default function NullBlock({
  kind,
  children,
}: {
  kind: "null" | "oos";
  children: React.ReactNode;
}) {
  return (
    <>
      <div className={styles.nullb}>
        <span className={styles.bt}>
          {kind === "null" ? "Khoa chưa công bố" : "Ngoài phạm vi hỗ trợ"}
        </span>
        {children}
      </div>
      <a className={styles.contact} href="mailto:khoatkt@uel.edu.vn">
        ✉ Hỏi văn phòng Khoa
      </a>
    </>
  );
}
