import type { Metadata } from 'next'
import ConditionalLayout from './conditional-layout'
import './globals.css'

export const metadata: Metadata = {
  title: 'نظام إدارة العيادة - AI Chat Bot',
  description: 'نظام إدارة العيادة مع بوت ذكي للرد على العملاء',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ar" dir="rtl" className="h-full">
      <body className="h-full antialiased">
        <ConditionalLayout>{children}</ConditionalLayout>
      </body>
    </html>
  )
}
