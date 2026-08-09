'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Sparkles, FileText, Settings, History, Database, CheckCircle, XCircle } from 'lucide-react'
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

interface ApprovalRequest {
  approval_id: string
  gate_type: string
  data: any
  status: string
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: 'Hello! I\'m your Autonomous Research Agent. I can help you with:\n\n- **Chat**: Multi-turn conversation with memory\n- **Research**: Deep, cited multi-agent research reports\n\nHow can I help you today?',
      timestamp: new Date()
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [mode, setMode] = useState<'chat' | 'research'>('chat')
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Poll pending workflow approvals
  useEffect(() => {
    async function checkApprovals() {
      try {
        const res = await fetch('http://localhost:8000/api/approvals')
        if (res.ok) {
          const data = await res.json()
          setApprovals(data.approvals || [])
        }
      } catch (err) {
        // Quiet fail if API server not running
      }
    }
    checkApprovals()
    const interval = setInterval(checkApprovals, 10000)
    return () => clearInterval(interval)
  }, [])

  async function handleApprovalResponse(approvalId: string, approved: boolean) {
    try {
      await fetch(`http://localhost:8000/api/approvals/${approvalId}/respond`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ approved, comments: approved ? 'Approved by user' : 'Rejected by user' })
      })
      setApprovals(prev => prev.filter(a => a.approval_id !== approvalId))
    } catch (err) {
      console.error('Failed to submit approval:', err)
    }
  }

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
        const response = await fetch('http://localhost:8000/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: input, mode: 'chat', session_id: 'default' })
        })
        const data = await response.json()
        
        const assistantMessage: Message = {
          role: 'assistant',
          content: data.response || 'Error: No response received',
          timestamp: new Date()
        }
        setMessages(prev => [...prev, assistantMessage])
      } else {
        const response = await fetch('http://localhost:8000/api/research', {
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
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
      {/* Sidebar */}
      <div className="w-64 bg-gray-100 dark:bg-gray-800 p-4 flex flex-col border-r border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2 mb-6">
          <Sparkles className="w-6 h-6 text-blue-600" />
          <h1 className="font-bold text-lg">Research Agent</h1>
        </div>
        
        <div className="space-y-2 mb-6">
          <button
            onClick={() => setMode('chat')}
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
            onClick={() => setMode('research')}
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
          <a href="/vault" className="w-full flex items-center gap-2 px-4 py-2 rounded-lg text-sm hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors">
            <Database className="w-4 h-4 text-purple-500" />
            Research Vault
          </a>
          <a href="/history" className="w-full flex items-center gap-2 px-4 py-2 rounded-lg text-sm hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors">
            <History className="w-4 h-4 text-amber-500" />
            History
          </a>
          <a href="/settings" className="w-full flex items-center gap-2 px-4 py-2 rounded-lg text-sm hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors">
            <Settings className="w-4 h-4 text-gray-500" />
            Settings
          </a>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Human Approval Notification Banner */}
        {approvals.length > 0 && (
          <div className="bg-amber-500 text-white px-6 py-3 flex justify-between items-center shadow-md">
            <div className="text-sm font-medium flex items-center gap-2">
              ⏳ Pending Workflow Approval ({approvals.length}): {approvals[0].gate_type.toUpperCase()} gate requires review.
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => handleApprovalResponse(approvals[0].approval_id, true)}
                className="flex items-center gap-1 px-3 py-1 bg-green-700 hover:bg-green-800 rounded text-xs font-semibold"
              >
                <CheckCircle className="w-3.5 h-3.5" /> Approve
              </button>
              <button
                onClick={() => handleApprovalResponse(approvals[0].approval_id, false)}
                className="flex items-center gap-1 px-3 py-1 bg-red-700 hover:bg-red-800 rounded text-xs font-semibold"
              >
                <XCircle className="w-3.5 h-3.5" /> Reject
              </button>
            </div>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4">
          <div className="max-w-4xl mx-auto space-y-4">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[85%] rounded-lg px-5 py-4 ${
                    message.role === 'user'
                      ? 'bg-blue-600 text-white shadow'
                      : 'bg-white dark:bg-gray-800 shadow border border-gray-200 dark:border-gray-700'
                  }`}
                >
                  {message.role === 'assistant' ? (
                    <div className="prose dark:prose-invert max-w-none text-sm leading-relaxed">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm, remarkMath]}
                        rehypePlugins={[rehypeKatex]}
                      >
                        {message.content}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    <p className="whitespace-pre-wrap text-sm">{message.content}</p>
                  )}
                  <div className="text-[10px] mt-2 opacity-60 text-right">
                    {message.timestamp.toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-white dark:bg-gray-800 shadow rounded-lg px-4 py-3 border border-gray-200 dark:border-gray-700">
                  <div className="flex items-center gap-3 text-xs text-gray-500">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" />
                      <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce delay-100" />
                      <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce delay-200" />
                    </div>
                    <span>{mode === 'research' ? 'Executing multi-agent research graph...' : 'Thinking...'}</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <div className="border-t border-gray-200 dark:border-gray-700 p-4 bg-white dark:bg-gray-800">
          <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={mode === 'chat' ? 'Ask any question or start a conversation...' : 'Enter deep research topic (e.g., Quantum Cryptography in 2026)...'}
                className="flex-1 px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-600 text-sm"
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
            <div className="text-xs text-gray-500 mt-2 flex justify-between">
              <span>Mode: <strong>{mode === 'chat' ? 'Multi-Turn Chat (with session memory)' : 'Deep Research (7-agent graph synthesis)'}</strong></span>
              <span>Proxy API: http://localhost:8000</span>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
