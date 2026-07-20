"use client";

import { Component, type ReactNode } from "react";
import styles from "./ErrorBoundary.module.css";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
}

/**
 * TIP-11.5: chặn lỗi ném từ cây component con, hiện fallback tĩnh có nút tải
 * lại thay vì màn hình trắng. Error Boundary phải là class component.
 */
export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: unknown) {
    // Log ra console để đối chiếu, không phá vỡ giao diện của người dùng
    console.error("[ErrorBoundary]", error);
  }

  handleReload = () => {
    if (typeof window !== "undefined") window.location.reload();
  };

  render() {
    if (!this.state.hasError) return this.props.children;
    return (
      <div className={styles.wrap} role="alert">
        <div className={styles.card}>
          <p className={styles.title}>Giao diện gặp trục trặc</p>
          <p className={styles.body}>
            Có lỗi ngoài dự tính khi hiển thị. Bạn tải lại trang giúp mình nhé,
            dữ liệu hội thoại chỉ nằm ở phiên này nên tải lại là sạch.
          </p>
          <button className={styles.button} onClick={this.handleReload}>
            Tải lại trang
          </button>
        </div>
      </div>
    );
  }
}
