import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'CodeWarden - Security & Observability Dashboard',
  description: 'Monitor your application security and errors in real-time',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-secondary-950 text-white antialiased">
        {children}
      </body>
    </html>
  );
}
