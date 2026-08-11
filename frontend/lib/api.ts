/** API helpers — all paths go through Next.js rewrites to the FastAPI backend. */

export const API_BASE = '' // relative → next.config rewrites /api/* → backend

export async function apiGet<T = any>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || res.statusText || `GET ${path} failed`)
  }
  return res.json()
}

export async function apiPost<T = any>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || res.statusText || `POST ${path} failed`)
  }
  // Stream responses leave body for caller
  const ct = res.headers.get('content-type') || ''
  if (ct.includes('text/event-stream')) {
    return res as unknown as T
  }
  return res.json()
}

export type ProgressSnapshot = {
  stage?: string
  status?: string
  finished?: boolean
  error?: string
  findings_count?: number
  factoids_count?: number
  sources_count?: number
  pages_scanned?: number
  elapsed_s?: number
  section_progress?: string
  sections?: { title: string; chars: number }[]
  report?: string
  markdown_path?: string
  query?: string
  job_id?: string
  mode?: string
  // Thinking panel (Deep Research style)
  learned?: string[]
  gaps?: string[]
  next_action?: string
  thoughts?: { ts?: number; kind?: string; text?: string }[]
  off_topic?: boolean
  plan?: Record<string, unknown>
}
