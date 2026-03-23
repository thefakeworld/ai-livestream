import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "YouTube直播监控",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body className="antialiased">{children}</body>
    </html>
  );
}
