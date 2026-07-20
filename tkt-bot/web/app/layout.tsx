import type { Metadata } from "next";
import { Fraunces, Be_Vietnam_Pro } from "next/font/google";
import "./globals.css";

// A2: Fraunces cho display/serif (câu hỏi, số lớn, blockquote), Be Vietnam Pro
// cho thân/UI. Phơi thành biến CSS --font-serif / --font-sans, next/font lo FOUT.
const serif = Fraunces({
  subsets: ["latin", "vietnamese"],
  weight: ["300", "400", "500", "600"],
  style: ["normal", "italic"],
  variable: "--font-serif",
  display: "swap",
});

const sans = Be_Vietnam_Pro({
  subsets: ["latin", "vietnamese"],
  weight: ["400", "500", "600"],
  variable: "--font-sans",
  display: "swap",
});

// TIP-13: staging mặc định noindex; đặt NEXT_PUBLIC_STAGING=0 khi lên production.
const IS_STAGING = process.env.NEXT_PUBLIC_STAGING !== "0";

export const metadata: Metadata = {
  title: "Khoa Toán Kinh tế UEL · Cổng hỏi đáp",
  description:
    "Trợ lý Khoa Toán Kinh tế: tuyển sinh, đào tạo, nghiên cứu và học vụ, mỗi con số đều dẫn nguồn kiểm chứng.",
  robots: IS_STAGING ? { index: false, follow: false } : undefined,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  // Dark mode là Phase 2 (Amendment REQ-08 v2, A1), TIP-12 chỉ hệ sáng.
  return (
    <html lang="vi" className={`${serif.variable} ${sans.variable}`}>
      <body>
        {IS_STAGING && (
          <div className="staging-banner">
            Bản thử nghiệm nội bộ · câu trả lời tổng hợp tự động từ nguồn công khai
            có dẫn nguồn
          </div>
        )}
        {children}
      </body>
    </html>
  );
}
