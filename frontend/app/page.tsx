'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Sparkles, FileText, Settings, History } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import 'katex/dist/katex.min.css'

interface Message {
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: 'Hello! I\'m your Autonomous Research Agent. I can help you with:\n\n- **Chat**: Quick answers and conversations\n- **Research**: Deep, cited research reports\n\nHow can I help you today?',
      timestamp: new Date()
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [mode, setMode] = useState<'chat' | 'research'>('chat')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      if (mode === 'chat') {
        const response = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: input, mode: 'chat' })
        })
        const data = await response.json()
        
        const assistantMessage: Message = {
          role: 'assistant',
          content: data.response || 'Error: No response received',
          timestamp: new Date()
        }
        setMessages(prev => [...prev, assistantMessage])
      } else {
        const response = await fetch('/api/research', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: input, mode: 'standard' })
        })
        const data = await response.json()
        
        const assistantMessage: Message = {
          role: 'assistant',
          content: data.report || 'Error: No report received',
          timestamp: new Date()
        }
        setMessages(prev => [...prev, assistantMessage])
      }
    } catch (error) {
      const errorMessage: Message = {
        role: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      {/* Sidebar */}
      <div className="w-64 bg-gray-100 dark:bg-gray-800 p-4 flex flex-col">
        <div className="flex items-center gap-2 mb-6">
          <Sparkles className="w-6 h-6 text-blue-600" />
          <h1 className="font-bold text-lg">Research Agent</h1>
        </div>
        
        <div className="space-y-2 mb-6">
          <button
            onClick={() => setMode('chat')}
            className={`w-full flex items-center gap-2 px-4 py-2 rounded-lg text-left transition-colors ${
              mode === 'chat' 
                ? 'bg-blue-600 text-white' 
                : 'hover:bg-gray-200 dark:hover:bg-gray-700'
            }`}
          >
            <Sparkles className="w-4 h-4" />
            Chat
          </button>
          <button
            onClick={() => setMode('research')}
            className={`w-full flex items-center gap-2 px-4 py-2 rounded-lg text-left transition-colors ${
              mode === 'research' 
                ? 'bg-blue-600 text-white' 
                : 'hover:bg-gray-200 dark:hover:bg-gray-700'
            }`}
          >
            <FileText className="w-4 h-4" />
            Research
          </button>
        </div>

        <div className="mt-auto space-y-2">
          <button className="w-full flex items-center gap-2 px-4 py-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors">
            <History className="w-4 h-4" />
            History
          </button>
          <button className="w-full flex items-center gap-2 px-4 py-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors">
            <Settings className="w-4 h-4" />
            Settings
          </button>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4">
          <div className="max-w-4xl mx-auto space-y-4">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-3 ${
                    message.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white dark:bg-gray-800 shadow-md'
                  }`}
                >
                  {message.role === 'assistant' ? (
                    <div className="prose dark:prose-invert max-w-none">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm, remarkMath]}
                        rehypePlugins={[rehypeKatex]}
                      >
                        {message.content}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  )}
                  <div className="text-xs mt-2 opacity-70">
                    {message.timestamp.toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-white dark:bg-gray-800 shadow-md rounded-lg px-4 py-3">
                  <div className="flex space-x-2">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100" />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200" />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <div className="border-t border-gray-200 dark:border-gray-700 p-4">
          <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={mode === 'chat' ? 'Type your message...' : 'Enter research topic...'}
                className="flex-1 px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-600"
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={isLoading || !input.trim()}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
            <div className="text-xs text-gray-500 mt-2">
              Mode: {mode === 'chat' ? 'Chat (quick responses)' : 'Research (deep, cited reports)'}
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
