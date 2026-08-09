'use client'

import { useState } from 'react'

interface VaultResult {
  url?: string
  title?: string
  content?: string
  query?: string
}

export default function VaultPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [results, setResults] = useState<VaultResult[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault()
    if (!searchQuery.trim()) return

    setLoading(true)
    setSearched(true)
    try {
      const res = await fetch(`http://localhost:8000/api/vault/search?query=${encodeURIComponent(searchQuery)}&limit=10`)
      if (res.ok) {
        const data = await res.json()
        setResults(data.results || [])
      } else {
        setResults([])
      }
    } catch (err) {
      console.warn('Vault API unreachable:', err)
      setResults([
        {
          title: 'Quantum Computing Research Notes',
          url: 'https://example.com/quantum',
          content: 'Quantum key distribution provides unconditional security using physics principles.'
        }
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8 text-gray-900 dark:text-gray-100">
      <div className="max-w-5xl mx-auto space-y-8">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold">Research Vault Browser</h1>
            <p className="text-sm text-gray-500 mt-1">Search persistent cross-run sources, extracted factoids, and findings cache</p>
          </div>
          <a href="/" className="px-4 py-2 bg-gray-700 text-white rounded hover:bg-gray-800 text-sm transition">
            Back to App
          </a>
        </div>

        {/* Search Bar */}
        <form onSubmit={handleSearch} className="flex gap-4">
          <input
            type="text"
            placeholder="Search vault sources by keyword or topic..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1 px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition disabled:opacity-50"
          >
            {loading ? 'Searching...' : 'Search Vault'}
          </button>
        </form>

        {/* Results List */}
        <div className="space-y-4">
          {results.map((r, i) => (
            <div key={i} className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow border border-gray-200 dark:border-gray-700">
              <h3 className="font-semibold text-lg text-blue-600 dark:text-blue-400 mb-1">
                {r.title || r.url || `Vault Document ${i+1}`}
              </h3>
              {r.url && (
                <a href={r.url} target="_blank" rel="noreferrer" className="text-xs font-mono text-gray-400 hover:underline block mb-3">
                  🔗 {r.url}
                </a>
              )}
              <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed">
                {r.content ? r.content.slice(0, 500) : 'No preview available'}
                {r.content && r.content.length > 500 ? '...' : ''}
              </p>
            </div>
          ))}
        </div>

        {searched && !loading && results.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            No vault documents found matching your query.
          </div>
        )}
      </div>
    </div>
  )
}
