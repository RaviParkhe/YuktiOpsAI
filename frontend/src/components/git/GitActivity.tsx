import React, { useState } from 'react'
import { 
  GitPullRequest, 
  GitCommit, 
  GitBranch, 
  CheckCircle2, 
  ExternalLink, 
  RefreshCw, 
  Link as LinkIcon 
} from 'lucide-react'
import type { GitEvent } from '../../types/models'

interface GitActivityProps {
  events: GitEvent[]
  repoConnected: boolean
  repoName: string
  onToggleConnection?: () => void
  onConfigureRepo?: () => void
  onTriggerTestWebhook?: () => void
}

export const GitActivity: React.FC<GitActivityProps> = ({
  events,
  repoConnected,
  repoName,
  onToggleConnection,
  onConfigureRepo,
  onTriggerTestWebhook,
}) => {
  const [activeTab, setActiveTab] = useState<'ALL' | 'PRS' | 'COMMITS'>('ALL')

  if (!repoConnected) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 text-center bg-[#090D16]">
        <div className="w-14 h-14 rounded-2xl bg-[#111925] border border-[#263246] flex items-center justify-center text-[#77869B] mb-5 shadow-xs">
          <GitBranch className="w-7 h-7" />
        </div>
        <h2 className="text-xl font-semibold text-[#F1F5F9] mb-2 font-sans">GitHub Repository Disconnected</h2>
        <p className="max-w-md text-xs text-[#A0AEC0] mb-6 leading-relaxed font-sans">
          No authorized GitHub repository is connected to this workspace. Webhook event ingestion and traceability links are paused.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-3">
          <button
            onClick={onToggleConnection}
            className="px-4 py-2 bg-[#62CBE8] hover:bg-[#79D6EE] text-[#07131C] text-xs font-semibold rounded-lg flex items-center gap-2 transition-colors font-sans"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Connect Repository {repoName ? `(${repoName})` : ''}</span>
          </button>
          {onConfigureRepo && (
            <button
              onClick={onConfigureRepo}
              className="px-4 py-2 bg-[#161F2D] hover:bg-[#263246] text-[#A0AEC0] hover:text-[#F1F5F9] border border-[#263246] text-xs font-medium rounded-lg transition-colors font-sans"
            >
              Configure Target
            </button>
          )}
        </div>
      </div>
    )
  }

  const filteredEvents = events.filter((e) => {
    if (activeTab === 'PRS') return e.type === 'PR'
    if (activeTab === 'COMMITS') return e.type === 'COMMIT'
    return true
  })

  return (
    <div className="h-full flex flex-col bg-[#090D16] overflow-hidden">
      {/* Top Banner: Connected Repository Info */}
      <div className="h-14 px-4 sm:px-6 border-b border-[#263246] flex flex-wrap items-center justify-between gap-4 bg-[#111925] shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-[#161F2D] border border-[#263246] flex items-center justify-center text-[#38B982]">
            <GitBranch className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-normal text-[#F1F5F9] text-sm sm:text-base font-display tracking-wide">Git Activity Feed</h1>
              <span className="text-[10px] font-sans px-2 py-0.5 rounded bg-[#38B982]/15 text-[#38B982] font-semibold border border-[#38B982]/30">
                Connected
              </span>
            </div>
            <div className="text-[11px] text-[#77869B] font-sans flex items-center gap-1.5 mt-0.5">
              <span>Repository: <strong className="font-mono text-[#A0AEC0]">{repoName}</strong></span>
              <span>·</span>
              <span>Branch: <span className="font-mono text-[#A0AEC0]">main</span></span>
              <span>·</span>
              <span>Webhooks active</span>
            </div>
          </div>
        </div>

        {/* Tab switcher */}
        <div className="flex items-center gap-1 bg-[#161F2D] p-1 rounded-lg border border-[#263246] text-xs font-sans">
          <button
            onClick={() => setActiveTab('ALL')}
            className={`px-3 py-1 rounded-md font-medium transition-all ${
              activeTab === 'ALL' ? 'bg-[#62CBE8] text-[#07131C] font-semibold' : 'text-[#A0AEC0] hover:text-[#F1F5F9]'
            }`}
          >
            All Activity ({events.length})
          </button>
          <button
            onClick={() => setActiveTab('PRS')}
            className={`px-3 py-1 rounded-md font-medium transition-all ${
              activeTab === 'PRS' ? 'bg-[#62CBE8] text-[#07131C] font-semibold' : 'text-[#A0AEC0] hover:text-[#F1F5F9]'
            }`}
          >
            Pull Requests ({events.filter(e => e.type === 'PR').length})
          </button>
          <button
            onClick={() => setActiveTab('COMMITS')}
            className={`px-3 py-1 rounded-md font-medium transition-all ${
              activeTab === 'COMMITS' ? 'bg-[#62CBE8] text-[#07131C] font-semibold' : 'text-[#A0AEC0] hover:text-[#F1F5F9]'
            }`}
          >
            Commits ({events.filter(e => e.type === 'COMMIT').length})
          </button>
        </div>
      </div>

      {/* Main Chronological Activity Feed */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 max-w-5xl mx-auto w-full">
        {events.length === 0 ? (
          <div className="h-full min-h-[320px] flex flex-col items-center justify-center p-8 text-center bg-[#111925] border border-[#263246] rounded-xl">
            <div className="w-12 h-12 rounded-xl bg-[#161F2D] border border-[#263246] flex items-center justify-center text-[#62CBE8] mb-4">
              <GitBranch className="w-6 h-6" />
            </div>
            <h3 className="text-base font-semibold text-[#F1F5F9] mb-1 font-sans">No Webhook Activity Recorded</h3>
            <p className="max-w-md text-xs text-[#A0AEC0] mb-5 leading-relaxed font-sans">
              Repository <strong className="text-[#F1F5F9] font-mono">{repoName || 'configured repo'}</strong> is connected, but no commit pushes or pull requests have arrived yet. When webhook events are received, they will be indexed here with task links and evidence verification.
            </p>
            <div className="flex flex-wrap items-center justify-center gap-3">
              {onTriggerTestWebhook && (
                <button
                  onClick={onTriggerTestWebhook}
                  className="px-4 py-2 bg-[#62CBE8] hover:bg-[#79D6EE] text-[#07131C] text-xs font-semibold rounded-lg flex items-center gap-2 transition-colors font-sans"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Dispatch Test Webhook Event</span>
                </button>
              )}
              {onConfigureRepo && (
                <button
                  onClick={onConfigureRepo}
                  className="px-4 py-2 bg-[#161F2D] hover:bg-[#263246] text-[#A0AEC0] hover:text-[#F1F5F9] border border-[#263246] text-xs font-medium rounded-lg transition-colors font-sans"
                >
                  <span>Integration Settings</span>
                </button>
              )}
            </div>
          </div>
        ) : filteredEvents.length === 0 ? (
          <div className="p-12 text-center bg-[#111925] rounded-xl border border-[#263246] space-y-2">
            <GitBranch className="w-8 h-8 text-[#77869B] mx-auto opacity-40" />
            <h4 className="text-sm font-semibold text-[#F1F5F9] font-sans">No {activeTab === 'PRS' ? 'Pull Requests' : 'Commits'} Found</h4>
            <p className="text-xs text-[#77869B] max-w-sm mx-auto font-sans">
              No events match the selected {activeTab.toLowerCase()} filter for {repoName}.
            </p>
          </div>
        ) : (
          <div className="bg-[#111925] border border-[#263246] rounded-xl overflow-hidden divide-y divide-[#263246]/60 shadow-xs">
            {filteredEvents.map((event) => (
              <div
                key={event.id}
                className="p-4 sm:p-5 hover:bg-[#161F2D]/50 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-4"
              >
                <div className="flex items-start gap-3.5 min-w-0">
                  {/* Event Type Icon */}
                  <div
                    className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 border mt-0.5 ${
                      event.type === 'PR'
                        ? event.prStatus === 'MERGED'
                          ? 'bg-[#161F2D] text-[#62CBE8] border-[#62CBE8]/30'
                          : 'bg-[#161F2D] text-[#38B982] border-[#38B982]/30'
                        : 'bg-[#161F2D] text-[#62CBE8] border-[#263246]'
                    }`}
                  >
                    {event.type === 'PR' ? (
                      <GitPullRequest className="w-4 h-4" />
                    ) : (
                      <GitCommit className="w-4 h-4" />
                    )}
                  </div>

                  <div className="min-w-0 space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-[10px] font-sans font-semibold px-2 py-0.5 rounded bg-[#161F2D] text-[#A0AEC0] border border-[#263246]">
                        {event.type}
                      </span>
                      {event.sha && (
                        <span className="text-xs font-mono text-[#62CBE8] bg-[#161F2D] px-2 py-0.5 rounded border border-[#263246]">
                          {event.sha}
                        </span>
                      )}
                      {event.prStatus && (
                        <span
                          className={`text-[10px] font-sans font-semibold px-2 py-0.5 rounded border ${
                            event.prStatus === 'MERGED'
                              ? 'bg-[#62CBE8]/15 text-[#62CBE8] border-[#62CBE8]/30'
                              : 'bg-[#38B982]/15 text-[#38B982] border-[#38B982]/30'
                          }`}
                        >
                          {event.prStatus}
                        </span>
                      )}
                      <span className="text-xs sm:text-sm font-semibold text-[#F1F5F9] font-sans truncate">
                        {event.title}
                      </span>
                    </div>

                    <div className="flex flex-wrap items-center gap-2 text-xs text-[#77869B] font-sans">
                      <span>Author: <span className="font-mono text-[#A0AEC0]">@{event.author}</span></span>
                      <span>·</span>
                      <span>Branch: <span className="font-mono text-[#A0AEC0]">{event.branch}</span></span>
                      <span>·</span>
                      <span className="font-mono text-[11px]">{event.timestamp}</span>
                    </div>

                    {/* Task Traceability Link */}
                    {event.linkedTaskId && (
                      <div className="pt-1.5 flex flex-wrap items-center gap-2">
                        <div className="inline-flex items-center gap-1.5 text-xs px-2.5 py-0.5 rounded bg-[#161F2D] border border-[#62CBE8]/30 text-[#62CBE8]">
                          <LinkIcon className="w-3 h-3" />
                          <span>Mapped to Task: <strong className="font-mono">{event.linkedTaskId}</strong></span>
                        </div>
                        {event.isEvidenceVerified && (
                          <span className="text-[11px] text-[#38B982] font-sans font-medium flex items-center gap-1">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>Verified Code Evidence</span>
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                {/* External GitHub Link */}
                <a
                  href={event.url}
                  target="_blank"
                  rel="noreferrer"
                  className="px-3 py-1.5 bg-[#161F2D] hover:bg-[#263246] text-xs font-sans font-medium text-[#A0AEC0] hover:text-[#F1F5F9] rounded-lg border border-[#263246] flex items-center gap-1.5 shrink-0 self-start sm:self-center transition-colors"
                >
                  <span>Open on GitHub</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default GitActivity
