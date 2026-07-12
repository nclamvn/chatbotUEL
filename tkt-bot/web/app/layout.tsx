import type { Metadata } from "next";
import { Be_Vietnam_Pro } from "next/font/google";
import "./globals.css";

const beVietnam = Be_Vietnam_Pro({
  weight: ["400", "500", "600", "700"],
  subsets: ["latin", "vietnamese"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Khoa Toán Kinh tế UEL · Cổng hỏi đáp",
  description:
    "Trợ lý Khoa Toán Kinh tế: tuyển sinh, đào tạo, nghiên cứu và học vụ, mỗi con số đều dẫn nguồn kiểm chứng.",
};

const themeInit = `(function(){try{var t=localStorage.getItem('tkt-theme');if(t==='dark'||(!t&&matchMedia('(prefers-color-scheme: dark)').matches)){document.documentElement.classList.add('dark')}}catch(e){}})()`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInit }} />
      </head>
      <body className={beVietnam.className}>{children}</body>
    </html>
  );
}
