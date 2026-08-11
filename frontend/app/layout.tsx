import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Providence — Deep Research Engine',
  description: 'Multi-agent deep research with verified evidence, cited reports, and honest research debt',
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
