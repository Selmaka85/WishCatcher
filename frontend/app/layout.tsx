import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'WishCatcher Studio | ASTRA Genesis',
  description: 'Context-aware unmet needs detection with pluggable AI, RAG and tools',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="ro"><body className="font-sans">{children}</body></html>
}
