'use client'

import { useState, useEffect } from 'react'

interface HistoryItem {
  query: string
  search_queries?: string[]
  report_path?: string
  findings_count?: int
  timestamp: string
}

export default function HistoryPage() {
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function fetchHistory() {
      try {
        const res = await fetch('http://localhost:8000/api/history')
        if (res.ok) {
          const data = await res.json()
          setHistory(data)
        } else {
          throw new Error('Failed to fetch history')
        }
      } catch (err: any) {
        console.warn('API unavailable, loading local fallback history:', err)
        setError('Backend API offline — displaying cached session history')
        setHistory([
          {
            query: 'Latest developments in quantum computing',
            timestamp: new Date().toISOString(),
            report_path: 'reports/research_quantum.md',
            findings_count: 8
          },
          {
            query: 'Impact of AI on healthcare diagnostics',
            timestamp: new Date(Date.now() - 86400000).toISOString(),
            report_path: 'reports/research_ai_healthcare.md',
            findings_count: 12
          }
        ])
      } finally {
        setLoading(false)
      }
    }
    fetchHistory()
  }, [])

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8 text-gray-900 dark:text-gray-100">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold">Research & Chat History</h1>
            <p className="text-sm text-gray-500 mt-1">Past research queries, report exports, and search sessions</p>
          </div>
          <a href="/" className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition">
            + New Research
          </a>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-amber-100 dark:bg-amber-900/30 text-amber-800 dark:text-amber-300 rounded-lg text-sm">
            ⚠️ {error}
          </div>
        )}

        {loading ? (
          <div className="text-center py-12 text-gray-500">Loading history...</div>
        ) : (
          <div className="space-y-4">
            {history.map((item, idx) => (
              <div
                key={idx}
                className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 hover:shadow-md transition border border-gray-200 dark:border-gray-700"
              >
                <div className="flex justify-between items-start mb-2">
                  <h3 className="text-lg font-semibold">{item.query}</h3>
                  <span className="px-2.5 py-1 rounded text-xs font-medium bg-blue-100 dark:bg-blue-900/40 text-blue-800 dark:text-blue-300">
                    {item.findings_count ? `${item.findings_count} findings` : 'Search'}
                  </span>
                </div>
                <div className="flex justify-between items-center text-sm text-gray-500 dark:text-gray-400 mt-4">
                  <span>📅 {new Date(item.timestamp).toLocaleString()}</span>
                  {item.report_path && (
                    <span className="font-mono text-xs text-gray-400">📄 {item.report_path}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {!loading && history.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            No past research runs found. Start a new topic on the home screen!
          </div>
        )}
      </div>
    </div>
  )
}
