'use client'

import { useState, useRef, useEffect } from 'react'
import { Send } from 'lucide-react'
import 'katex/dist/katex.min.css'
import {
  Sidebar,
  ProgressBanner,
  MessageBubble,
  ApprovalBanner,
  LoadingDots,
  PlanEditor,
} from '@/components'
import type { ChatMessage, ApprovalRequest, ResearchPlanPayload } from '@/components'
import { apiGet, apiPost, type ProgressSnapshot } from '@/lib/api'

async function apiPut<T = any>(path: string, body: unknown): Promise<T> {
  const res = await fetch(path, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || res.statusText || `PUT ${path} failed`)
  }
  return res.json()
}

export default function Home() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content:
        "Hello! I'm **Providence**, your deep-research engine. I can help with:\n\n- **Chat**: multi-turn conversation with memory (streaming)\n- **Research**: multi-agent cited reports with live progress\n- **Evidence**: every claim verified against this run's sources\n\nHow can I help you today?",
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [mode, setMode] = useState<'chat' | 'research'>('chat')
  const [researchMode, setResearchMode] = useState('standard')
  const [autonomy, setAutonomy] = useState('L1')
  const [planFirst, setPlanFirst] = useState(false)
  const [pendingPlan, setPendingPlan] = useState<ResearchPlanPayload | null>(null)
  const [planBusy, setPlanBusy] = useState(false)
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([])
  const [progressStatus, setProgressStatus] = useState('')
  const [thinking, setThinking] = useState<{
    learned: string[]
    gaps: string[]
    nextAction: string
    thoughts: { kind?: string; text?: string }[]
    pagesScanned?: number
    sourcesCount?: number
    findingsCount?: number
    offTopic?: boolean
    stage?: string
  }>({ learned: [], gaps: [], nextAction: '', thoughts: [] })
  const messagesEndRef = useRef<HTMLDivElement>(null)

  async function pollResearchJob(jobId: string, userText: string) {
    let finished = false
    for (let i = 0; i < 900 && !finished; i++) {
      await new Promise((r) => setTimeout(r, 1000))
      try {
        let snap: ProgressSnapshot
        if (jobId) {
          try {
            const job = await apiGet<ProgressSnapshot & { status?: string }>(
              `/api/jobs/${jobId}`
            )
            // L2 plan pause
            if (job.status === 'awaiting_plan') {
              setProgressStatus('Awaiting plan approval…')
              // try to load plan from thoughts or list
              const plans = await apiGet<{ plans?: ResearchPlanPayload[] }>(
                '/api/research/plans?limit=5'
              ).catch(() => ({ plans: [] }))
              const match = (plans.plans || []).find((p) => p.job_id === jobId) ||
                (plans.plans || [])[0]
              if (match) {
                setPendingPlan(match)
                setIsLoading(false)
                return
              }
            }
            snap = {
              ...job,
              finished:
                job.finished ||
                ['complete', 'error', 'aborted'].includes(job.status || ''),
              status: job.status || job.stage,
            }
          } catch {
            snap = await apiGet('/api/research/progress')
          }
        } else {
          snap = await apiGet('/api/research/progress')
        }
        const label = snap.status || snap.stage || 'running'
        const secs = snap.section_progress || ''
        setProgressStatus(
          `${label}${secs ? ` · sections ${secs}` : ''}${
            snap.findings_count ? ` · findings ${snap.findings_count}` : ''
          } · ${snap.elapsed_s || 0}s`
        )
        setThinking({
          learned: snap.learned || [],
          gaps: snap.gaps || [],
          nextAction: snap.next_action || '',
          thoughts: snap.thoughts || [],
          pagesScanned: snap.pages_scanned,
          sourcesCount: snap.sources_count,
          findingsCount: snap.findings_count,
          offTopic: snap.off_topic,
          stage: snap.stage,
        })
        finished = !!snap.finished
        if (snap.error && finished) throw new Error(snap.error)
      } catch (pollErr) {
        if (
          pollErr instanceof Error &&
          pollErr.message &&
          !pollErr.message.includes('Failed')
        ) {
          if (
            pollErr.message.includes('aborted') ||
            pollErr.message.includes('Ship gate')
          ) {
            throw pollErr
          }
        }
      }
    }

    let finalSnap: ProgressSnapshot = {}
    if (jobId) {
      finalSnap = await apiGet(`/api/jobs/${jobId}`).catch(() => ({}))
    }
    if (!finalSnap.report) {
      finalSnap = await apiGet('/api/research/progress').catch(() => ({}))
    }
    let lastReport = finalSnap.report || ''
    if (!lastReport) {
      lastReport =
        `## Research complete\n\n**Query:** ${userText}\n\n**Mode:** ${researchMode}\n\n` +
        `Findings: ${finalSnap.findings_count || 0} · Elapsed: ${finalSnap.elapsed_s || 0}s\n\n` +
        `_Path: ${finalSnap.markdown_path || 'reports/'}_`
    } else if (finalSnap.markdown_path) {
      lastReport += `\n\n---\n_Saved: \`${finalSnap.markdown_path}\`_`
    }

    setMessages((prev) => [
      ...prev,
      { role: 'assistant', content: lastReport, timestamp: new Date() },
    ])
    setProgressStatus('')
    setThinking({ learned: [], gaps: [], nextAction: '', thoughts: [] })
  }

  async function handlePlanApprove(edited: {
    outline: { title: string }[]
    search_queries: string[]
    clarifications?: Record<string, string>
  }) {
    if (!pendingPlan) return
    setPlanBusy(true)
    try {
      await apiPut(`/api/research/plans/${pendingPlan.plan_id}`, {
        outline: edited.outline,
        search_queries: edited.search_queries,
        clarifications: edited.clarifications,
        plan: {
          ...(pendingPlan.plan || {}),
          outline: edited.outline,
          search_queries: edited.search_queries,
        },
      })
      const runRes = await apiPost<{ job_id?: string; status?: string }>(
        `/api/research/plans/${pendingPlan.plan_id}/run`,
        { background: true, clarifications: edited.clarifications }
      )
      setPendingPlan(null)
      setIsLoading(true)
      setProgressStatus('Plan approved — researching…')
      setThinking({
        learned: [],
        gaps: [],
        nextAction: 'Gathering sources with approved plan',
        thoughts: [],
      })
      await pollResearchJob(runRes?.job_id || '', pendingPlan.query)
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `Plan run failed: ${err instanceof Error ? err.message : 'unknown'}`,
          timestamp: new Date(),
        },
      ])
    } finally {
      setPlanBusy(false)
      setIsLoading(false)
      setProgressStatus('')
    }
  }

  useEffect(() => {
    apiGet<{ mode?: string; autonomy?: string }>('/api/settings')
      .then((data) => {
        if (data?.mode) setResearchMode(data.mode)
        if (data?.autonomy) setAutonomy(data.autonomy)
      })
      .catch(() => {})
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, progressStatus])

  useEffect(() => {
    async function checkApprovals() {
      try {
        const data = await apiGet<{ approvals?: ApprovalRequest[] }>('/api/approvals')
        setApprovals(data.approvals || [])
      } catch {
        /* quiet */
      }
    }
    checkApprovals()
    const interval = setInterval(checkApprovals, 10000)
    return () => clearInterval(interval)
  }, [])

  async function handleApprovalResponse(approvalId: string, approved: boolean) {
    try {
      await apiPost(`/api/approvals/${approvalId}/respond`, {
        approved,
        comments: approved ? 'Approved by user' : 'Rejected by user',
      })
      setApprovals((prev) => prev.filter((a) => a.approval_id !== approvalId))
    } catch (err) {
      console.error('Failed to submit approval:', err)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userText = input
    setMessages((prev) => [
      ...prev,
      { role: 'user', content: userText, timestamp: new Date() },
    ])
    setInput('')
    setIsLoading(true)
    setProgressStatus('')

    try {
      if (mode === 'chat') {
        const response = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: userText,
            mode: 'fast',
            session_id: 'default',
            stream: true,
            escalate: true,
          }),
        })

        const contentType = response.headers.get('content-type') || ''
        if (contentType.includes('text/event-stream') && response.body) {
          const reader = response.body.getReader()
          const decoder = new TextDecoder()
          let acc = ''
          setMessages((prev) => [
            ...prev,
            { role: 'assistant', content: '', timestamp: new Date() },
          ])
          let buffer = ''
          while (true) {
            const { done, value } = await reader.read()
            if (done) break
            buffer += decoder.decode(value, { stream: true })
            const parts = buffer.split('\n\n')
            buffer = parts.pop() || ''
            for (const part of parts) {
              const line = part.trim()
              if (!line.startsWith('data: ')) continue
              try {
                const evt = JSON.parse(line.slice(6))
                if (evt.type === 'token') {
                  acc += evt.text || ''
                  setMessages((prev) => {
                    const copy = [...prev]
                    copy[copy.length - 1] = {
                      role: 'assistant',
                      content: acc,
                      timestamp: new Date(),
                    }
                    return copy
                  })
                } else if (evt.type === 'done' && evt.text) {
                  acc = evt.text
                  setMessages((prev) => {
                    const copy = [...prev]
                    copy[copy.length - 1] = {
                      role: 'assistant',
                      content: acc,
                      timestamp: new Date(),
                    }
                    return copy
                  })
                } else if (evt.type === 'error') {
                  throw new Error(evt.error || 'stream error')
                }
              } catch (parseErr) {
                if (parseErr instanceof SyntaxError) continue
                throw parseErr
              }
            }
          }
        } else {
          const data = await response.json()
          setMessages((prev) => [
            ...prev,
            {
              role: 'assistant',
              content: data.response || 'Error: No response received',
              timestamp: new Date(),
            },
          ])
        }
      } else {
        setProgressStatus('Starting research...')
        setThinking({ learned: [], gaps: [], nextAction: 'Planning…', thoughts: [] })
        setPendingPlan(null)

        // L2 required plan review; L1 optional via planFirst toggle
        const wantPlan = planFirst || autonomy === 'L2'
        if (wantPlan) {
          setProgressStatus('Generating editable research plan…')
          const planRes = await apiPost<ResearchPlanPayload>('/api/research/plans', {
            query: userText,
            mode: researchMode,
            autonomy,
          })
          setPendingPlan(planRes)
          setMessages((prev) => [
            ...prev,
            {
              role: 'assistant',
              content:
                `## Research plan ready\n\n` +
                `**Plan ID:** \`${planRes.plan_id}\`\n\n` +
                `Review the outline and search queries below, then click **Approve & research**.` +
                (planRes.needs_clarification
                  ? `\n\n_Query looks ambiguous — answer clarifying questions if you can._`
                  : ''),
              timestamp: new Date(),
            },
          ])
          setProgressStatus('')
          setIsLoading(false)
          return
        }

        const startRes = await apiPost<{ job_id?: string }>('/api/research', {
          query: userText,
          mode: researchMode,
          autonomy,
          background: true,
          skip_clarify: true,
        })
        const jobId = startRes?.job_id || ''
        await pollResearchJob(jobId, userText)
      }
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
          timestamp: new Date(),
        },
      ])
      setProgressStatus('')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
      <Sidebar mode={mode} onModeChange={setMode} />

      <div className="flex-1 flex flex-col">
        <ApprovalBanner approvals={approvals} onRespond={handleApprovalResponse} />
        <ProgressBanner
          status={progressStatus}
          visible={!!progressStatus}
          learned={thinking.learned}
          gaps={thinking.gaps}
          nextAction={thinking.nextAction}
          thoughts={thinking.thoughts}
          pagesScanned={thinking.pagesScanned}
          sourcesCount={thinking.sourcesCount}
          findingsCount={thinking.findingsCount}
          offTopic={thinking.offTopic}
          stage={thinking.stage}
        />

        <div className="flex-1 overflow-y-auto p-4">
          <div className="max-w-4xl mx-auto space-y-4">
            {messages.map((message, index) => (
              <MessageBubble key={index} message={message} />
            ))}
            {pendingPlan && (
              <PlanEditor
                plan={pendingPlan}
                busy={planBusy}
                onCancel={() => {
                  setPendingPlan(null)
                  setMessages((prev) => [
                    ...prev,
                    {
                      role: 'assistant',
                      content: 'Plan cancelled. Submit a new research query when ready.',
                      timestamp: new Date(),
                    },
                  ])
                }}
                onApprove={handlePlanApprove}
              />
            )}
            {isLoading && (
              <LoadingDots
                label={
                  mode === 'research'
                    ? progressStatus || 'Executing multi-agent research graph...'
                    : 'Streaming response...'
                }
              />
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        <div className="border-t border-gray-200 dark:border-gray-700 p-4 bg-white dark:bg-gray-800">
          <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={
                  mode === 'chat'
                    ? 'Ask any question or start a conversation...'
                    : 'Enter deep research topic...'
                }
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
            <div className="text-xs text-gray-500 mt-2 flex flex-wrap justify-between items-center gap-2">
              <span>
                Mode:{' '}
                <strong>
                  {mode === 'chat'
                    ? 'Multi-Turn Chat (streaming)'
                    : `Deep Research (${researchMode} / ${autonomy})`}
                </strong>
              </span>
              {mode === 'research' && (
                <div className="flex gap-2">
                  <select
                    value={researchMode}
                    onChange={(e) => setResearchMode(e.target.value)}
                    className="text-xs border rounded px-2 py-1 bg-white dark:bg-gray-900"
                  >
                    <option value="quick">quick</option>
                    <option value="standard">standard</option>
                    <option value="deep">deep</option>
                    <option value="academic">academic</option>
                    <option value="recency">recency</option>
                    <option value="compare">compare</option>
                    <option value="ultra-long">ultra-long</option>
                  </select>
                  <select
                    value={autonomy}
                    onChange={(e) => setAutonomy(e.target.value)}
                    className="text-xs border rounded px-2 py-1 bg-white dark:bg-gray-900"
                  >
                    <option value="L1">L1 auto</option>
                    <option value="L2">L2 plan review</option>
                    <option value="L3">L3 hard budget</option>
                  </select>
                  <label className="flex items-center gap-1 text-xs cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={planFirst || autonomy === 'L2'}
                      disabled={autonomy === 'L2'}
                      onChange={(e) => setPlanFirst(e.target.checked)}
                      className="rounded"
                    />
                    Edit plan first
                  </label>
                </div>
              )}
              <span className="opacity-0 select-none text-[10px]">&#8203;</span>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
