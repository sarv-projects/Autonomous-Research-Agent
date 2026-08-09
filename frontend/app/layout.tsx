import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Autonomous Research Agent',
  description: 'Self-improving research and chat agent with cited reports',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
