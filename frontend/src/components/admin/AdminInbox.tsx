import React from 'react'
import { 
  ShieldCheck, 
  AlertTriangle, 
  CheckCircle2, 
  XCircle, 
  MessageSquare, 
  ArrowRight, 
  Lock, 
  Check, 
  Clock,
  Sparkles
} from 'lucide-react'
import type { AIProposal } from '../../types/models'
import type { UserRole } from '../../types/auth'

interface AdminInboxProps {
  userRole: UserRole
  proposals: AIProposal[]
  onApproveProposal: (proposalId: string) => void
  onRejectProposal: (proposalId: string) => void
  onNavigateToTasks: () => void
}

export const AdminInbox: React.FC<AdminInboxProps> = ({
  userRole,
  proposals,
  onApproveProposal,
  onRejectProposal,
  onNavigateToTasks,
}) => {
  // ROLE GATING: If non-admin attempts to access, show clean 403 screen
  if (userRole !== 'ADMIN') {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 text-center bg-[#090D16]">
        <div className="w-14 h-14 rounded-2xl bg-[#111925] border border-[#263246] flex items-center justify-center text-[#E47777] mb-5 shadow-xs">
          <Lock className="w-7 h-7" />
        </div>
        <h2 className="text-xl font-semibold text-[#F1F5F9] mb-2 font-sans">403 — Administrative Area Restricted</h2>
        <p className="max-w-md text-xs text-[#A0AEC0] mb-6 leading-relaxed font-sans">
          The <strong>AI &amp; Admin Decision Queue</strong> is restricted to Project Administrators. You are currently logged in as a <strong>Developer</strong>.
        </p>
        <div className="bg-[#111925] border border-[#263246] p-4 rounded-xl text-xs font-mono text-[#77869B] max-w-sm mb-6 text-left space-y-1">
          <div className="text-[#F1F5F9] font-medium mb-1">Authorization Policy:</div>
          <div>• Active Role: DEVELOPER</div>
          <div>• Required Role: ADMIN</div>
          <div>• Action: Blocker Approvals &amp; Board Mutating Directives</div>
        </div>
        <button
          onClick={onNavigateToTasks}
          className="px-4 py-2 bg-[#62CBE8] hover:bg-[#79D6EE] text-[#07131C] text-xs font-semibold rounded-lg flex items-center gap-2 transition-colors font-sans"
        >
          <span>Return to Task Board</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>
    )
  }

  const pendingProposals = proposals.filter((p) => p.status === 'PENDING')
  const resolvedProposals = proposals.filter((p) => p.status !== 'PENDING')

  return (
    <div className="h-full overflow-y-auto p-4 sm:p-6 bg-[#090D16]">
      {/* Header */}
      <div className="max-w-5xl mx-auto mb-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#263246]">
          <div>
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-[#111925] border border-[#263246] flex items-center justify-center text-[#E5B85C]">
                <ShieldCheck className="w-4 h-4" />
              </div>
              <h1 className="text-lg sm:text-xl font-normal text-[#F1F5F9] tracking-wide font-display">AI &amp; Admin Decision Inbox</h1>
            </div>
            <p className="text-xs text-[#77869B] mt-1 font-sans">
              Review AI-detected blockers and status recommendations. The AI proposes; the Project Lead decides.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs font-sans px-2.5 py-1 rounded-md bg-[#111925] border border-[#263246] text-[#E5B85C] font-semibold">
              Pending Decisions: {pendingProposals.length}
            </span>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto space-y-6">
        {/* Pending Proposals Section */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-xs font-semibold font-sans uppercase tracking-wider text-[#A0AEC0] flex items-center gap-2">
              <Sparkles className="w-3.5 h-3.5 text-[#62CBE8]" />
              <span>Pending Action Proposals ({pendingProposals.length})</span>
            </h2>
            <span className="text-xs text-[#77869B] font-sans">Requires human authorization</span>
          </div>

          {pendingProposals.length === 0 ? (
            <div className="bg-[#111925] border border-[#263246] rounded-xl p-8 text-center">
              <CheckCircle2 className="w-8 h-8 text-[#38B982] mx-auto mb-2" />
              <h3 className="text-sm font-semibold text-[#F1F5F9] mb-1 font-sans">Decision Queue Clear</h3>
              <p className="text-xs text-[#77869B] font-sans">
                All AI-detected blockers have been reviewed and resolved. No pending items.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {pendingProposals.map((proposal) => (
                <div
                  key={proposal.id}
                  className="bg-[#111925] border border-[#263246] hover:border-[#62CBE8]/40 rounded-xl p-5 shadow-xs transition-all space-y-4"
                >
                  {/* Top Bar of Card */}
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div className="flex items-center gap-2.5">
                      <span className="px-2 py-0.5 bg-[#E47777]/15 text-[#E47777] border border-[#E47777]/30 rounded font-sans text-[11px] font-semibold flex items-center gap-1.5">
                        <AlertTriangle className="w-3 h-3" />
                        PROPOSED: {proposal.proposedStatus}
                      </span>
                      <span className="font-mono text-xs text-[#62CBE8] font-semibold bg-[#161F2D] px-2 py-0.5 rounded border border-[#263246]">
                        {proposal.taskId}
                      </span>
                      <span className="text-xs sm:text-sm font-semibold text-[#F1F5F9] font-sans">
                        {proposal.taskTitle}
                      </span>
                    </div>

                    {proposal.confidence && (
                      <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-[#161F2D] text-[#38B982] border border-[#38B982]/30">
                        Confidence: {proposal.confidence}%
                      </span>
                    )}
                  </div>

                  {/* AI Reason */}
                  <div>
                    <div className="text-[11px] font-semibold uppercase text-[#77869B] tracking-wider mb-1 font-sans">
                      Identified Risk &amp; Reason
                    </div>
                    <p className="text-xs text-[#F1F5F9] font-medium leading-relaxed font-sans">
                      {proposal.reason}
                    </p>
                  </div>

                  {/* Quoted Chat Evidence Box */}
                  <div className="bg-[#161F2D] border border-[#263246] rounded-lg p-3.5 space-y-2">
                    <div className="flex items-center justify-between text-xs text-[#77869B] font-sans">
                      <span className="flex items-center gap-1.5 font-medium text-[#A0AEC0]">
                        <MessageSquare className="w-3.5 h-3.5 text-[#62CBE8]" />
                        Source Evidence ({proposal.evidenceMessage.channel})
                      </span>
                      <span className="text-[10px] font-mono">{proposal.evidenceMessage.timestamp}</span>
                    </div>
                    <blockquote className="text-xs font-mono text-[#E5B85C] bg-[#090D16] p-2.5 rounded border border-[#263246]">
                      &quot;{proposal.evidenceMessage.quote}&quot;
                    </blockquote>
                    <div className="text-[11px] text-[#77869B] font-sans">
                      Author: <span className="text-[#F1F5F9] font-medium">{proposal.evidenceMessage.authorName}</span> (<span className="font-mono text-[#A0AEC0]">@{proposal.evidenceMessage.authorHandle}</span>)
                    </div>
                  </div>

                  {/* Suggested Next Action */}
                  <div className="p-3 rounded-lg bg-[#161F2D] border border-[#263246] flex items-start gap-2 text-xs text-[#A0AEC0]">
                    <Sparkles className="w-3.5 h-3.5 text-[#E5B85C] shrink-0 mt-0.5" />
                    <div>
                      <span className="font-semibold text-[#F1F5F9]">Recommendation: </span>
                      <span>{proposal.suggestedAction}</span>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-[#263246]">
                    <div className="text-[11px] text-[#77869B] font-sans">
                      Approving updates the Task Board status and commits to the Audit Ledger.
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => onRejectProposal(proposal.id)}
                        className="px-3.5 py-1.5 bg-[#161F2D] hover:bg-[#263246] text-[#E47777] border border-[#E47777]/40 text-xs font-medium rounded-lg flex items-center gap-1.5 transition-colors font-sans"
                      >
                        <XCircle className="w-3.5 h-3.5" />
                        <span>Reject &amp; Dismiss</span>
                      </button>
                      <button
                        onClick={() => onApproveProposal(proposal.id)}
                        className="px-4 py-1.5 bg-[#38B982] hover:bg-[#2ea571] text-[#07131C] text-xs font-semibold rounded-lg flex items-center gap-1.5 shadow-xs transition-colors font-sans"
                      >
                        <Check className="w-3.5 h-3.5" />
                        <span>Approve &amp; Update Task</span>
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Resolved Proposals / Audit History */}
        {resolvedProposals.length > 0 && (
          <div className="pt-4 border-t border-[#263246]">
            <h2 className="text-xs font-semibold font-sans uppercase tracking-wider text-[#77869B] mb-3 flex items-center gap-2">
              <Clock className="w-3.5 h-3.5 text-[#77869B]" />
              <span>Resolved Decision Ledger ({resolvedProposals.length})</span>
            </h2>

            <div className="space-y-2">
              {resolvedProposals.map((item) => (
                <div
                  key={item.id}
                  className="bg-[#111925] border border-[#263246] rounded-lg p-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 text-xs"
                >
                  <div className="flex items-center gap-2.5">
                    <span
                      className={`px-2 py-0.5 rounded font-sans font-semibold text-[10px] border ${
                        item.status === 'APPROVED'
                          ? 'bg-[#38B982]/15 text-[#38B982] border-[#38B982]/30'
                          : 'bg-[#E47777]/15 text-[#E47777] border-[#E47777]/30'
                      }`}
                    >
                      {item.status}
                    </span>
                    <span className="font-mono text-[#62CBE8] font-semibold text-[11px]">{item.taskId}</span>
                    <span className="text-[#F1F5F9] font-medium font-sans">{item.taskTitle}</span>
                  </div>

                  <div className="text-[#77869B] font-sans text-[11px]">
                    Reviewed by Lead
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default AdminInbox
