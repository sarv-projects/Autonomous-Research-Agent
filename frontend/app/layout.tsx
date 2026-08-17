import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Providence — Deep Research Engine',
  description: 'Autonomous multi-agent deep research with verified citations, adversarial critique, and a strict compiler ship-gate. Zero API keys required.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="font-sans antialiased">{children}</body>
    </html>
  )
}
