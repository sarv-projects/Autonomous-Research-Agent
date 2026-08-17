'use client'

interface LoadingDotsProps {
  label?: string
}

export function LoadingDots({ label = 'Loading...' }: LoadingDotsProps) {
  return (
    <div className="flex justify-start">
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg px-4 py-3 border border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-3 text-xs text-gray-500">
          <div className="flex space-x-1">
            <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
            <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
            <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
          <span>{label}</span>
        </div>
      </div>
    </div>
  )
}
