'use client'

interface ProgressBannerProps {
  status: string
  visible?: boolean
  learned?: string[]
  gaps?: string[]
  nextAction?: string
  thoughts?: { kind?: string; text?: string }[]
  pagesScanned?: number
  sourcesCount?: number
  findingsCount?: number
  offTopic?: boolean
  stage?: string
}

export function ProgressBanner({
  status,
  visible = true,
  learned = [],
  gaps = [],
  nextAction = '',
  thoughts = [],
  pagesScanned,
  sourcesCount,
  findingsCount,
  offTopic,
  stage,
}: ProgressBannerProps) {
  if (!visible || !status) return null

  const recentThoughts = thoughts.slice(-6)

  return (
    <div className="bg-blue-50 dark:bg-blue-900/30 border-b border-blue-200 dark:border-blue-800 px-6 py-3 text-xs text-blue-900 dark:text-blue-100 space-y-2">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
        <span className="font-semibold">Progress:</span>
        <span>{status}</span>
        {stage && <span className="opacity-70">· {stage}</span>}
        {typeof findingsCount === 'number' && findingsCount > 0 && (
          <span className="opacity-80">· findings {findingsCount}</span>
        )}
        {typeof sourcesCount === 'number' && sourcesCount > 0 && (
          <span className="opacity-80">· sources {sourcesCount}</span>
        )}
        {typeof pagesScanned === 'number' && pagesScanned > 0 && (
          <span className="opacity-80">· pages {pagesScanned}</span>
        )}
        {offTopic && (
          <span className="text-amber-700 dark:text-amber-300 font-medium">· off-topic recovery</span>
        )}
      </div>

      {(nextAction || learned.length > 0 || gaps.length > 0 || recentThoughts.length > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-1 border-t border-blue-200/60 dark:border-blue-700/50">
          <div>
            <div className="font-semibold text-[11px] uppercase tracking-wide opacity-70 mb-1">
              Next action
            </div>
            <div className="text-[11px] leading-snug">
              {nextAction || '—'}
            </div>
          </div>
          <div>
            <div className="font-semibold text-[11px] uppercase tracking-wide opacity-70 mb-1">
              Learned
            </div>
            <ul className="list-disc pl-4 space-y-0.5 text-[11px] leading-snug max-h-20 overflow-y-auto">
              {(learned.slice(-4).length ? learned.slice(-4) : ['—']).map((item, i) => (
                <li key={i}>{typeof item === 'string' ? item : '—'}</li>
              ))}
            </ul>
          </div>
          <div>
            <div className="font-semibold text-[11px] uppercase tracking-wide opacity-70 mb-1">
              Gaps
            </div>
            <ul className="list-disc pl-4 space-y-0.5 text-[11px] leading-snug max-h-20 overflow-y-auto">
              {(gaps.slice(-4).length ? gaps.slice(-4) : ['—']).map((item, i) => (
                <li key={i}>{typeof item === 'string' ? item : '—'}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {recentThoughts.length > 0 && (
        <div className="pt-1 border-t border-blue-200/40 dark:border-blue-700/40">
          <div className="font-semibold text-[11px] uppercase tracking-wide opacity-70 mb-1">
            Thinking stream
          </div>
          <div className="flex flex-col gap-0.5 max-h-16 overflow-y-auto">
            {recentThoughts.map((t, i) => (
              <div key={i} className="text-[11px] opacity-90">
                <span className="font-medium opacity-60">[{t.kind || 'note'}]</span>{' '}
                {t.text || ''}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
