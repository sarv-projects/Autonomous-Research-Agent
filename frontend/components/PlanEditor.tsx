'use client'

import { useState, useEffect } from 'react'
import { CheckCircle, XCircle, Pencil } from 'lucide-react'

export type ResearchPlanPayload = {
  plan_id: string
  query: string
  mode?: string
  autonomy?: string
  status?: string
  plan?: {
    topic?: string
    subtopics?: string[]
    outline?: { title?: string; queries?: string[] }[]
    search_queries?: string[]
    rationale?: string
    assumptions?: string[]
    refined_query_hint?: string
  }
  outline?: { title?: string; order?: number }[]
  search_queries?: string[]
  clarifying_questions?: string[]
  needs_clarification?: boolean
  job_id?: string
}

interface PlanEditorProps {
  plan: ResearchPlanPayload
  onApprove: (edited: {
    outline: { title: string }[]
    search_queries: string[]
    clarifications?: Record<string, string>
  }) => void
  onCancel: () => void
  busy?: boolean
}

export function PlanEditor({ plan, onApprove, onCancel, busy }: PlanEditorProps) {
  const initialOutline =
    plan.outline?.map((o) => o.title || '') ||
    plan.plan?.outline?.map((o) => o.title || '') ||
    []
  const initialQueries =
    plan.search_queries || plan.plan?.search_queries || []

  const [outlineText, setOutlineText] = useState(initialOutline.join('\n'))
  const [queriesText, setQueriesText] = useState(initialQueries.join('\n'))
  const [answers, setAnswers] = useState<Record<string, string>>({})

  useEffect(() => {
    setOutlineText(initialOutline.join('\n'))
    setQueriesText(initialQueries.join('\n'))
  }, [plan.plan_id])

  const questions = plan.clarifying_questions || []

  const handleApprove = () => {
    const outline = outlineText
      .split('\n')
      .map((t) => t.trim())
      .filter(Boolean)
      .map((title) => ({ title }))
    const search_queries = queriesText
      .split('\n')
      .map((t) => t.trim())
      .filter(Boolean)
    const clarifications =
      Object.keys(answers).length > 0 ? answers : undefined
    onApprove({ outline, search_queries, clarifications })
  }

  return (
    <div className="border border-amber-300 dark:border-amber-700 rounded-lg bg-amber-50 dark:bg-amber-950/40 p-4 space-y-3 text-sm">
      <div className="flex items-center gap-2 font-semibold text-amber-900 dark:text-amber-100">
        <Pencil className="w-4 h-4" />
        Editable research plan
        <span className="font-normal opacity-70 text-xs">
          ({plan.plan_id} · {plan.status || 'draft'})
        </span>
      </div>

      <div className="text-xs text-amber-900/80 dark:text-amber-100/80">
        <strong>Topic:</strong> {plan.plan?.topic || plan.query}
      </div>
      {plan.plan?.rationale && (
        <div className="text-xs opacity-80">{plan.plan.rationale}</div>
      )}

      {plan.needs_clarification && questions.length > 0 && (
        <div className="space-y-2 border-t border-amber-200 dark:border-amber-800 pt-2">
          <div className="font-medium text-xs uppercase tracking-wide opacity-70">
            Clarifying questions
          </div>
          {questions.map((q, i) => (
            <div key={i} className="space-y-1">
              <label className="text-xs block">{q}</label>
              <input
                className="w-full px-2 py-1 rounded border border-amber-300 dark:border-amber-700 bg-white dark:bg-gray-900 text-xs"
                value={answers[q] || ''}
                onChange={(e) =>
                  setAnswers((prev) => ({ ...prev, [q]: e.target.value }))
                }
                placeholder="Your answer (optional)"
                disabled={busy}
              />
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div>
          <label className="text-xs font-medium uppercase tracking-wide opacity-70 block mb-1">
            Outline (one section per line)
          </label>
          <textarea
            className="w-full h-36 px-2 py-1 rounded border border-amber-300 dark:border-amber-700 bg-white dark:bg-gray-900 text-xs font-mono"
            value={outlineText}
            onChange={(e) => setOutlineText(e.target.value)}
            disabled={busy}
          />
        </div>
        <div>
          <label className="text-xs font-medium uppercase tracking-wide opacity-70 block mb-1">
            Search queries (one per line)
          </label>
          <textarea
            className="w-full h-36 px-2 py-1 rounded border border-amber-300 dark:border-amber-700 bg-white dark:bg-gray-900 text-xs font-mono"
            value={queriesText}
            onChange={(e) => setQueriesText(e.target.value)}
            disabled={busy}
          />
        </div>
      </div>

      <div className="flex gap-2 justify-end">
        <button
          type="button"
          onClick={onCancel}
          disabled={busy}
          className="flex items-center gap-1 px-3 py-1.5 rounded text-xs bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600"
        >
          <XCircle className="w-3.5 h-3.5" /> Cancel
        </button>
        <button
          type="button"
          onClick={handleApprove}
          disabled={busy}
          className="flex items-center gap-1 px-3 py-1.5 rounded text-xs bg-green-700 hover:bg-green-800 text-white font-semibold disabled:opacity-50"
        >
          <CheckCircle className="w-3.5 h-3.5" />
          {busy ? 'Starting…' : 'Approve & research'}
        </button>
      </div>
    </div>
  )
}
