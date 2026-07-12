"use client";

import styles from "./ModeToggle.module.css";

export default function ModeToggle() {
  const toggle = () => {
    const dark = document.documentElement.classList.toggle("dark");
    try {
      localStorage.setItem("tkt-theme", dark ? "dark" : "light");
    } catch {
      // môi trường chặn localStorage thì theme chỉ sống trong phiên
    }
  };
  return (
    <button className={styles.mode} onClick={toggle} aria-label="Đổi giao diện sáng tối">
      ◐
    </button>
  );
}
