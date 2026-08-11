'use client'

import { CheckCircle, XCircle } from 'lucide-react'

export interface ApprovalRequest {
  approval_id: string
  gate_type: string
  data?: any
  status?: string
}

interface ApprovalBannerProps {
  approvals: ApprovalRequest[]
  onRespond: (id: string, approved: boolean) => void
}

export function ApprovalBanner({ approvals, onRespond }: ApprovalBannerProps) {
  if (!approvals.length) return null
  const a = approvals[0]
  return (
    <div className="bg-amber-500 text-white px-6 py-3 flex justify-between items-center shadow-md">
      <div className="text-sm font-medium flex items-center gap-2">
        ⏳ Pending Workflow Approval ({approvals.length}): {a.gate_type.toUpperCase()} gate
        requires review.
      </div>
      <div className="flex gap-2">
        <button
          onClick={() => onRespond(a.approval_id, true)}
          className="flex items-center gap-1 px-3 py-1 bg-green-700 hover:bg-green-800 rounded text-xs font-semibold"
        >
          <CheckCircle className="w-3.5 h-3.5" /> Approve
        </button>
        <button
          onClick={() => onRespond(a.approval_id, false)}
          className="flex items-center gap-1 px-3 py-1 bg-red-700 hover:bg-red-800 rounded text-xs font-semibold"
        >
          <XCircle className="w-3.5 h-3.5" /> Reject
        </button>
      </div>
    </div>
  )
}
