import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'SmartGrowth AI — Customer Intelligence Platform',
  description: 'End-to-end ML platform for customer intelligence, churn prediction, demand forecasting and NLP insights.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}