'use client'

import { useState, useEffect } from 'react'
import { apiGet } from '@/lib/api'

interface HistoryItem {
  query: string
  search_queries?: string[]
  report_path?: string
  findings_count?: number
  timestamp: string
}

interface ReportItem {
  name: string
  path: string
  format: string
  size_bytes: number
  modified: string
}

export default function HistoryPage() {
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [reports, setReports] = useState<ReportItem[]>([])
  const [preview, setPreview] = useState<{ name: string; content: string } | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function load() {
      try {
        const [h, r] = await Promise.all([
          apiGet<HistoryItem[]>('/api/history?limit=30').catch(() => []),
          apiGet<{ reports: ReportItem[] }>('/api/reports?limit=40').catch(() => ({ reports: [] })),
        ])
        setHistory(Array.isArray(h) ? h : [])
        setReports(r.reports || [])
      } catch (err: any) {
        setError(err.message || 'Failed to load history')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  async function openReport(name: string) {
    try {
      const data = await apiGet<{ name: string; content: string }>(
        `/api/reports/${encodeURIComponent(name)}`
      )
      setPreview({ name: data.name, content: data.content })
    } catch (err: any) {
      setError(err.message || 'Failed to open report')
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8 text-gray-900 dark:text-gray-100">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold">Research History & Reports</h1>
            <p className="text-sm text-gray-500 mt-1">
              Past queries and generated reports on disk
            </p>
          </div>
          <a
            href="/"
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
          >
            + New Research
          </a>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-amber-100 dark:bg-amber-900/30 text-amber-800 dark:text-amber-300 rounded-lg text-sm">
            ⚠️ {error}
          </div>
        )}

        {loading ? (
          <div className="text-center py-12 text-gray-500">Loading...</div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div>
              <h2 className="text-xl font-semibold mb-4">Search history</h2>
              <div className="space-y-3">
                {history.map((item, idx) => (
                  <div
                    key={idx}
                    className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 border border-gray-200 dark:border-gray-700"
                  >
                    <h3 className="font-semibold">{item.query}</h3>
                    <div className="flex justify-between text-xs text-gray-500 mt-2">
                      <span>{item.timestamp}</span>
                      <span>{item.findings_count ?? 0} findings</span>
                    </div>
                    {item.report_path && (
                      <p className="font-mono text-xs text-gray-400 mt-1 truncate">
                        {item.report_path}
                      </p>
                    )}
                  </div>
                ))}
                {!history.length && (
                  <p className="text-sm text-gray-500">No history yet.</p>
                )}
              </div>
            </div>

            <div>
              <h2 className="text-xl font-semibold mb-4">Reports on disk</h2>
              <div className="space-y-2 max-h-[70vh] overflow-y-auto">
                {reports.map((r) => (
                  <button
                    key={r.name}
                    onClick={() => openReport(r.name)}
                    className="w-full text-left bg-white dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-700 hover:border-blue-500 transition text-sm"
                  >
                    <div className="font-medium truncate">{r.name}</div>
                    <div className="text-xs text-gray-500 mt-1 flex justify-between">
                      <span>{r.format}</span>
                      <span>{r.modified}</span>
                      <span>{Math.round(r.size_bytes / 1024)} KB</span>
                    </div>
                  </button>
                ))}
                {!reports.length && (
                  <p className="text-sm text-gray-500">No reports in reports/ yet.</p>
                )}
              </div>
            </div>
          </div>
        )}

        {preview && (
          <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div className="bg-white dark:bg-gray-900 rounded-xl max-w-4xl w-full max-h-[85vh] overflow-hidden flex flex-col shadow-2xl">
              <div className="flex justify-between items-center px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                <h3 className="font-semibold truncate pr-4">{preview.name}</h3>
                <button
                  onClick={() => setPreview(null)}
                  className="px-3 py-1 bg-gray-200 dark:bg-gray-700 rounded text-sm"
                >
                  Close
                </button>
              </div>
              <pre className="p-6 overflow-y-auto text-xs whitespace-pre-wrap flex-1">
                {preview.content}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
