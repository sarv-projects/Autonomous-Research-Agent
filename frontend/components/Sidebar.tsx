'use client'

import { Sparkles, FileText, Settings, History, Database } from 'lucide-react'

type Mode = 'chat' | 'research'

interface SidebarProps {
  mode: Mode
  onModeChange: (m: Mode) => void
}

export function Sidebar({ mode, onModeChange }: SidebarProps) {
  return (
    <div className="w-64 bg-gray-100 dark:bg-gray-800 p-4 flex flex-col border-r border-gray-200 dark:border-gray-700">
      <div className="flex items-center gap-2 mb-6">
        <Sparkles className="w-6 h-6 text-blue-600" />
        <h1 className="font-bold text-lg">Providence</h1>
      </div>

      <div className="space-y-2 mb-6">
        <button
          onClick={() => onModeChange('chat')}
          className={`w-full flex items-center gap-2 px-4 py-2.5 rounded-lg text-left transition-colors font-medium text-sm ${
            mode === 'chat'
              ? 'bg-blue-600 text-white shadow'
              : 'hover:bg-gray-200 dark:hover:bg-gray-700'
          }`}
        >
          <Sparkles className="w-4 h-4" />
          Chat
        </button>
        <button
          onClick={() => onModeChange('research')}
          className={`w-full flex items-center gap-2 px-4 py-2.5 rounded-lg text-left transition-colors font-medium text-sm ${
            mode === 'research'
              ? 'bg-blue-600 text-white shadow'
              : 'hover:bg-gray-200 dark:hover:bg-gray-700'
          }`}
        >
          <FileText className="w-4 h-4" />
          Deep Research
        </button>
      </div>

      <div className="mt-auto space-y-2 pt-4 border-t border-gray-200 dark:border-gray-700">
        <a
          href="/vault"
          className="w-full flex items-center gap-2 px-4 py-2 rounded-lg text-sm hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
        >
          <Database className="w-4 h-4 text-purple-500" />
          Research Vault
        </a>
        <a
          href="/history"
          className="w-full flex items-center gap-2 px-4 py-2 rounded-lg text-sm hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
        >
          <History className="w-4 h-4 text-amber-500" />
          History
        </a>
        <a
          href="/settings"
          className="w-full flex items-center gap-2 px-4 py-2 rounded-lg text-sm hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
        >
          <Settings className="w-4 h-4 text-gray-500" />
          Settings
        </a>
      </div>
    </div>
  )
}
