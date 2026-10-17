import React, { useState } from 'react'
import { 
  GitBranch, 
  CheckCircle2, 
  RefreshCw, 
  ExternalLink, 
  Database, 
  MessageSquare, 
  Zap, 
  Key,
  Check,
  Copy
} from 'lucide-react'

interface IntegrationsViewProps {
  repoConnected: boolean
  repoName: string
  onToggleConnection: () => void
  onTriggerSync: () => void
  onSaveRepoName?: (name: string) => void
}

export const IntegrationsView: React.FC<IntegrationsViewProps> = ({
  repoConnected,
  repoName,
  onToggleConnection,
  onTriggerSync,
  onSaveRepoName,
}) => {
  const [copied, setCopied] = useState(false)
  const [isSyncing, setIsSyncing] = useState(false)
  const [isEditingRepo, setIsEditingRepo] = useState(false)
  const [repoInput, setRepoInput] = useState(repoName || '')

  const handleCopyWebhook = () => {
    navigator.clipboard.writeText('https://api.yuktiops.dev/v1/webhooks/github')
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleSync = () => {
    setIsSyncing(true)
    setTimeout(() => {
      setIsSyncing(false)
      onTriggerSync()
    }, 700)
  }

  const handleSaveRepo = (e: React.FormEvent) => {
    e.preventDefault()
    if (repoInput.trim() && onSaveRepoName) {
      onSaveRepoName(repoInput.trim())
      setIsEditingRepo(false)
    }
  }

  return (
    <div className="h-full overflow-y-auto p-4 sm:p-6 bg-[#090D16]">
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#263246]">
          <div>
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-[#111925] border border-[#263246] flex items-center justify-center text-[#38B982]">
                <Zap className="w-4 h-4" />
              </div>
              <h1 className="text-lg sm:text-xl font-normal text-[#F1F5F9] tracking-wide font-display">Connected Integrations</h1>
            </div>
            <p className="text-xs text-[#77869B] mt-1 font-sans">
              Live Webhooks · NLP Standup Classifier · PostgreSQL Memory Layer
            </p>
          </div>

          <button
            onClick={handleSync}
            disabled={isSyncing || !repoConnected}
            className="px-3.5 py-1.5 bg-[#161F2D] hover:bg-[#263246] disabled:opacity-40 text-[#F1F5F9] border border-[#263246] text-xs font-sans font-medium rounded-lg flex items-center gap-2 transition-colors self-start sm:self-auto shadow-xs"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-[#62CBE8] ${isSyncing ? 'animate-spin' : ''}`} />
            <span>{isSyncing ? 'Verifying Sync...' : 'Test Webhooks'}</span>
          </button>
        </div>

        {/* Integration Cards */}
        <div className="space-y-4">
          {/* Card 1: GitHub Repository Integration */}
          <div className="bg-[#111925] border border-[#263246] rounded-xl p-5 shadow-xs space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-start gap-3.5">
                <div className="w-10 h-10 rounded-lg bg-[#161F2D] border border-[#263246] flex items-center justify-center text-[#38B982] shrink-0">
                  <GitBranch className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-semibold text-[#F1F5F9] font-sans">GitHub Repository Integration</h3>
                    <span className={`text-[10px] font-sans px-2 py-0.5 rounded font-semibold border ${
                      repoConnected
                        ? 'bg-[#38B982]/15 text-[#38B982] border-[#38B982]/30'
                        : 'bg-[#E47777]/15 text-[#E47777] border-[#E47777]/30'
                    }`}>
                      {repoConnected ? 'Connected · Webhooks Active' : 'Disconnected'}
                    </span>
                  </div>
                  <p className="text-xs text-[#A0AEC0] mt-1 font-sans">
                    Bi-directional webhook synchronization for Pull Requests, commits, branches, and review states.
                  </p>
                </div>
              </div>

              <button
                onClick={onToggleConnection}
                className={`px-3.5 py-1.5 text-xs font-sans font-medium rounded-lg border transition-colors shrink-0 ${
                  repoConnected
                    ? 'bg-[#161F2D] hover:bg-[#E47777]/20 text-[#E47777] border-[#E47777]/30'
                    : 'bg-[#38B982] hover:bg-[#2ea571] text-[#07131C] border-[#38B982] font-semibold'
                }`}
              >
                {repoConnected ? 'Disconnect Repo' : 'Authorize Repository'}
              </button>
            </div>

            {/* Technical Parameters */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-3 border-t border-[#263246] text-xs">
              <div className="p-3 bg-[#161F2D] rounded-lg border border-[#263246] space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-[#77869B] text-[11px] font-sans block">Repository Target</span>
                  {onSaveRepoName && (
                    <button
                      type="button"
                      onClick={() => setIsEditingRepo(!isEditingRepo)}
                      className="text-[#62CBE8] hover:underline text-[10px] font-sans"
                    >
                      {isEditingRepo ? 'Cancel' : 'Change Target'}
                    </button>
                  )}
                </div>
                {isEditingRepo ? (
                  <form onSubmit={handleSaveRepo} className="flex items-center gap-1.5">
                    <input
                      type="text"
                      value={repoInput}
                      onChange={(e) => setRepoInput(e.target.value)}
                      placeholder="org/repo-name"
                      className="bg-[#090D16] border border-[#263246] px-2 py-1 text-xs text-[#F1F5F9] rounded outline-none flex-1 font-mono"
                    />
                    <button
                      type="submit"
                      className="px-2 py-1 bg-[#62CBE8] text-[#07131C] font-semibold text-xs rounded hover:bg-[#79D6EE]"
                    >
                      Save
                    </button>
                  </form>
                ) : (
                  <span className="text-[#F1F5F9] font-medium flex items-center gap-1.5">
                    <span>{repoName ? `github.com/${repoName}` : 'No target configured'}</span>
                    {repoName && <ExternalLink className="w-3 h-3 text-[#62CBE8]" />}
                  </span>
                )}
              </div>

              <div className="p-3 bg-[#161F2D] rounded-lg border border-[#263246] space-y-1">
                <span className="text-[#77869B] text-[11px] block">Webhook Ingestion Endpoint</span>
                <div className="flex items-center justify-between">
                  <span className="text-[#F1F5F9] truncate max-w-[260px]">
                    https://api.yuktiops.dev/v1/webhooks/github
                  </span>
                  <button onClick={handleCopyWebhook} className="text-[#62CBE8] hover:text-white transition-colors" title="Copy endpoint URL">
                    {copied ? <Check className="w-3.5 h-3.5 text-[#38B982]" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Card 2: Team Messaging Bridge (Hinglish/NLP Classifier) */}
          <div className="bg-[#111925] border border-[#263246] rounded-xl p-5 shadow-xs space-y-4">
            <div className="flex items-start gap-3.5">
              <div className="w-10 h-10 rounded-lg bg-[#161F2D] border border-[#263246] flex items-center justify-center text-[#62CBE8] shrink-0">
                <MessageSquare className="w-5 h-5" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-semibold text-[#F1F5F9] font-sans">Team Chat &amp; Natural Language Classifier</h3>
                  <span className="text-[10px] font-sans px-2 py-0.5 rounded font-semibold bg-[#62CBE8]/15 text-[#62CBE8] border border-[#62CBE8]/30">
                    Online · NLP Parser Active
                  </span>
                </div>
                <p className="text-xs text-[#A0AEC0] mt-1 font-sans">
                  Parses informal standups, Slack, and Discord messages in English and Hinglish. Automatically detects dependency blockers and links chat quotes to active tasks.
                </p>
              </div>
            </div>

            <div className="p-3 bg-[#161F2D] rounded-lg border border-[#263246] flex flex-wrap items-center justify-between gap-3 text-xs font-sans">
              <div className="flex items-center gap-2 text-[#77869B]">
                <Key className="w-3.5 h-3.5 text-[#62CBE8]" />
                <span>Detection Confidence Threshold:</span>
                <strong className="text-[#F1F5F9] font-mono">85% Minimum</strong>
              </div>
              <span className="text-[#38B982] font-medium flex items-center gap-1 text-[11px]">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Grounding Verification Active</span>
              </span>
            </div>
          </div>

          {/* Card 3: PostgreSQL Vector Memory Layer */}
          <div className="bg-[#111925] border border-[#263246] rounded-xl p-5 shadow-xs space-y-4">
            <div className="flex items-start gap-3.5">
              <div className="w-10 h-10 rounded-lg bg-[#161F2D] border border-[#263246] flex items-center justify-center text-[#62CBE8] shrink-0">
                <Database className="w-5 h-5" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-semibold text-[#F1F5F9] font-sans">Project Memory Store &amp; Decision Ledger</h3>
                  <span className="text-[10px] font-sans px-2 py-0.5 rounded font-semibold bg-[#38B982]/15 text-[#38B982] border border-[#38B982]/30">
                    Persistence Active
                  </span>
                </div>
                <p className="text-xs text-[#A0AEC0] mt-1 font-sans">
                  Maintains the immutable ledger of approved leader decisions, audit trail timestamps, task ownership changes, and sprint state.
                </p>
              </div>
            </div>

            <div className="p-3 bg-[#161F2D] rounded-lg border border-[#263246] text-xs font-sans text-[#77869B] flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <span>Storage Key: <strong className="text-[#F1F5F9] font-mono">yuktiops_workspace_data_v2</strong></span>
              <span>Backend Bridge: <strong className="text-[#A0AEC0]">Local Client Engine Active</strong></span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default IntegrationsView
