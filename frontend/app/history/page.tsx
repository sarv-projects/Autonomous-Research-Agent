import { Metadata } from 'next'
import { redirect } from 'next/navigation'

export const metadata: Metadata = {
  title: 'History - Autonomous Research Agent',
  description: 'View your past research and chat history',
}

export default function HistoryPage() {
  // TODO: Fetch actual history from API
  const history = [
    {
      id: 1,
      query: 'Latest developments in quantum computing',
      timestamp: '2024-01-15T10:30:00Z',
      mode: 'research',
      status: 'completed'
    },
    {
      id: 2,
      query: 'Impact of AI on healthcare',
      timestamp: '2024-01-14T15:45:00Z',
      mode: 'research',
      status: 'completed'
    },
    {
      id: 3,
      query: 'Explain machine learning basics',
      timestamp: '2024-01-13T09:00:00Z',
      mode: 'chat',
      status: 'completed'
    }
  ]

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Research & Chat History</h1>
        
        <div className="space-y-4">
          {history.map((item) => (
            <div
              key={item.id}
              className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer"
            >
              <div className="flex justify-between items-start mb-2">
                <h3 className="text-lg font-semibold">{item.query}</h3>
                <span className={`px-2 py-1 rounded text-xs ${
                  item.mode === 'research' ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800'
                }`}>
                  {item.mode}
                </span>
              </div>
              <div className="text-sm text-gray-500">
                {new Date(item.timestamp).toLocaleString()}
              </div>
            </div>
          ))}
        </div>

        {history.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            No history yet. Start a conversation or research!
          </div>
        )}
      </div>
    </div>
  )
}
