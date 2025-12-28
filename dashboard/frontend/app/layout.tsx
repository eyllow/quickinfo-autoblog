import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'QuickInfo Dashboard',
  description: '반자동/자동 통합 발행 대시보드',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body className="min-h-screen bg-background text-foreground">
        {children}
      </body>
    </html>
  );
}
