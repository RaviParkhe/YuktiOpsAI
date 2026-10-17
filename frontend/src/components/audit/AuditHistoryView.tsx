import React, { useState } from 'react'
import { 
  Clock, 
  CheckCircle2, 
  XCircle, 
  MessageSquare, 
  Search, 
  Filter,
  ShieldCheck,
  UserCheck
} from 'lucide-react'
import type { AIProposal } from '../../types/models'
import type { User } from '../../types/auth'

interface AuditHistoryViewProps {
  proposals: AIProposal[]
  currentUser?: User
  onSelectTask: (taskId: string) => void
}

export const AuditHistoryView: React.FC<AuditHistoryViewProps> = ({
  proposals,
  currentUser,
  onSelectTask,
}) => {
  const [filterStatus, setFilterStatus] = useState<'ALL' | 'APPROVED' | 'REJECTED' | 'PENDING'>('ALL')
  const [searchQuery, setSearchQuery] = useState('')

  const filteredProposals = proposals.filter((p) => {
    if (filterStatus !== 'ALL' && p.status !== filterStatus) return false
    if (!searchQuery.trim()) return true
    const q = searchQuery.toLowerCase()
    return (
      p.taskId.toLowerCase().includes(q) ||
      p.taskTitle.toLowerCase().includes(q) ||
      p.reason.toLowerCase().includes(q)
    )
  })

  return (
    <div className="h-full overflow-y-auto p-4 sm:p-6 bg-[#090D16]">
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#263246]">
          <div>
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-[#111925] border border-[#263246] flex items-center justify-center text-[#62CBE8]">
                <Clock className="w-4 h-4" />
              </div>
              <h1 className="text-lg sm:text-xl font-normal text-[#F1F5F9] tracking-wide font-display">Audit Decision Ledger</h1>
            </div>
            <p className="text-xs text-[#77869B] mt-1 font-sans">
              Immutable Human-in-the-Loop Approval History &amp; Traceability
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-sans px-2.5 py-1 rounded-md bg-[#111925] border border-[#263246] text-[#62CBE8] font-semibold">
              Total Entries: {proposals.length}
            </span>
          </div>
        </div>

        {/* Search & Filters */}
        <div className="flex flex-col sm:flex-row gap-2.5">
          <div className="relative flex-1 bg-[#111925] border border-[#263246] rounded-lg flex items-center px-3 focus-within:border-[#62CBE8]/60 transition-colors">
            <Search className="w-3.5 h-3.5 text-[#77869B]" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by task ID, title, or reasoning..."
              className="w-full bg-transparent text-xs text-[#F1F5F9] placeholder-[#77869B] px-2.5 py-2 outline-none font-sans"
            />
          </div>

          <div className="flex items-center gap-1.5 bg-[#111925] px-2.5 py-2 rounded-lg border border-[#263246] text-xs font-sans">
            <Filter className="w-3.5 h-3.5 text-[#77869B]" />
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value as typeof filterStatus)}
              className="bg-transparent text-[#F1F5F9] outline-none cursor-pointer font-sans"
            >
              <option value="ALL" className="bg-[#111925]">All Decisions</option>
              <option value="APPROVED" className="bg-[#111925]">Approved Only</option>
              <option value="REJECTED" className="bg-[#111925]">Rejected Only</option>
              <option value="PENDING" className="bg-[#111925]">Pending Only</option>
            </select>
          </div>
        </div>

        {/* Audit Log Entries List */}
        {proposals.length === 0 ? (
          <div className="bg-[#111925] border border-[#263246] rounded-xl p-10 text-center space-y-3">
            <div className="w-12 h-12 rounded-xl bg-[#161F2D] border border-[#263246] flex items-center justify-center text-[#62CBE8] mx-auto mb-2">
              <Clock className="w-6 h-6" />
            </div>
            <h3 className="text-base font-semibold text-[#F1F5F9] font-sans">Audit Decision Ledger Empty</h3>
            <p className="text-xs text-[#A0AEC0] max-w-md mx-auto leading-relaxed font-sans">
              No blocker approval entries have been recorded yet. When lead engineers approve or reject AI-detected blocker proposals in the Decision Inbox, immutable audit records with evidence quotes and timestamps will be logged here.
            </p>
          </div>
        ) : filteredProposals.length === 0 ? (
          <div className="p-10 text-center bg-[#111925] rounded-xl border border-[#263246] space-y-2">
            <Clock className="w-8 h-8 text-[#77869B] mx-auto opacity-40" />
            <h4 className="text-sm font-semibold text-[#F1F5F9] font-sans">No Matching Audit Entries</h4>
            <p className="text-xs text-[#77869B] max-w-sm mx-auto font-sans">
              No blocker approval entries match your current search and filter criteria.
            </p>
          </div>
        ) : (
          <div className="bg-[#111925] border border-[#263246] rounded-xl overflow-hidden divide-y divide-[#263246]/60 shadow-xs">
            {filteredProposals.map((item) => (
              <div
                key={item.id}
                className="p-5 hover:bg-[#161F2D]/50 transition-colors space-y-3"
              >
                {/* Header row */}
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center gap-2.5">
                    <span className={`px-2 py-0.5 rounded font-sans text-[10px] font-semibold flex items-center gap-1 border ${
                      item.status === 'APPROVED'
                        ? 'bg-[#38B982]/15 text-[#38B982] border-[#38B982]/30'
                        : item.status === 'REJECTED'
                        ? 'bg-[#E47777]/15 text-[#E47777] border-[#E47777]/30'
                        : 'bg-[#E5B85C]/15 text-[#E5B85C] border-[#E5B85C]/30'
                    }`}>
                      {item.status === 'APPROVED' && <CheckCircle2 className="w-3 h-3" />}
                      {item.status === 'REJECTED' && <XCircle className="w-3 h-3" />}
                      {item.status === 'PENDING' && <Clock className="w-3 h-3" />}
                      <span>{item.status}</span>
                    </span>

                    <button
                      onClick={() => onSelectTask(item.taskId)}
                      className="font-mono text-xs text-[#62CBE8] hover:underline bg-[#161F2D] px-2 py-0.5 rounded border border-[#263246] font-semibold"
                    >
                      {item.taskId}
                    </button>

                    <span className="text-xs sm:text-sm font-semibold text-[#F1F5F9] font-sans">
                      {item.taskTitle}
                    </span>
                  </div>

                  <div className="text-xs text-[#77869B] font-sans">
                    Target: <strong className="font-mono text-[#F1F5F9]">{item.proposedStatus}</strong>
                  </div>
                </div>

                {/* Reason & Action */}
                <div className="text-xs text-[#A0AEC0] leading-relaxed font-sans">
                  <strong className="text-[#F1F5F9]">Audit Finding: </strong>
                  {item.reason}
                </div>

                {/* Quoted Evidence */}
                {item.evidenceMessage && (
                  <div className="p-3 bg-[#161F2D] border border-[#263246] rounded-lg text-xs space-y-1.5 font-sans">
                    <div className="flex items-center justify-between text-[#77869B] text-[11px]">
                      <span className="flex items-center gap-1 text-[#62CBE8]">
                        <MessageSquare className="w-3 h-3" />
                        <span>Source: {item.evidenceMessage.channel}</span>
                      </span>
                      <span className="font-mono text-[10px]">{item.evidenceMessage.timestamp}</span>
                    </div>
                    <blockquote className="text-[#E5B85C] font-mono bg-[#090D16] p-2.5 rounded border border-[#263246]">
                      &quot;{item.evidenceMessage.quote}&quot;
                    </blockquote>
                    <div className="text-[11px] text-[#77869B]">
                      Reported by: <span className="text-[#F1F5F9]">{item.evidenceMessage.authorName}</span> (<span className="font-mono text-[#A0AEC0]">@{item.evidenceMessage.authorHandle}</span>)
                    </div>
                  </div>
                )}

                {/* Footer Reviewer Meta */}
                <div className="pt-2.5 border-t border-[#263246]/60 flex flex-wrap items-center justify-between gap-3 text-xs text-[#77869B] font-sans">
                  <div className="flex items-center gap-1.5">
                    <UserCheck className="w-3.5 h-3.5 text-[#38B982]" />
                    <span>Decision Authority: <strong className="text-[#F1F5F9]">{currentUser ? `Project Lead (${currentUser.name})` : 'Project Lead'}</strong></span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <ShieldCheck className="w-3.5 h-3.5 text-[#62CBE8]" />
                    <span>Verified Audit Ledger Entry</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default AuditHistoryView
