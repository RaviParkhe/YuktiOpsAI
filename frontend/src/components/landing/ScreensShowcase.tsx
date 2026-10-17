import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Activity, 
  MessageSquare, 
  Kanban, 
  GitBranch, 
  ShieldCheck, 
  ExternalLink, 
  AlertTriangle 
} from 'lucide-react'

interface ScreensShowcaseProps {
  onLaunchWorkspace: () => void
}

export const ScreensShowcase: React.FC<ScreensShowcaseProps> = ({ onLaunchWorkspace }) => {
  const [activeTab, setActiveTab] = useState<'command' | 'chat' | 'tasks' | 'git' | 'inbox'>('command')

  const TABS = [
    { id: 'command', label: 'Command Center', icon: Activity, tag: 'OPERATIONS' },
    { id: 'chat', label: 'Team Conversations', icon: MessageSquare, tag: 'INTELLIGENCE' },
    { id: 'tasks', label: 'Task Management', icon: Kanban, tag: 'COORDINATION' },
    { id: 'git', label: 'GitHub Activity', icon: GitBranch, tag: 'TRACEABILITY' },
    { id: 'inbox', label: 'Decision Inbox', icon: ShieldCheck, tag: 'GOVERNANCE' },
  ] as const

  return (
    <section id="workspace" className="py-24 px-6 bg-[#090D16] border-b border-[#263246]">
      <div className="max-w-6xl mx-auto space-y-12">
        {/* Section Header */}
        <div className="text-center space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded bg-[#111925] border border-[#263246] text-xs font-sans font-medium text-[#62CBE8]">
            <span className="w-1.5 h-1.5 rounded-full bg-[#62CBE8]" />
            <span>UNIFIED WORKSPACE</span>
          </div>
          <h2 className="font-display text-xl sm:text-3xl text-[#F1F5F9] tracking-wide font-normal">
            Unified Workspace
          </h2>
          <p className="text-sm sm:text-base text-[#A0AEC0] max-w-2xl mx-auto font-sans font-normal">
            Unifies project context across real components rather than isolated views: Project Command Center, Team Conversations, Task Management, GitHub Activity, AI Recommendations &amp; Decision Inbox.
          </p>
        </div>

        {/* Tab Selectors */}
        <div className="flex items-center justify-center gap-2 sm:gap-3 flex-wrap">
          {TABS.map((tab) => {
            const Icon = tab.icon
            const isActive = activeTab === tab.id
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-2.5 rounded-xl text-xs font-sans font-medium transition-all flex items-center gap-2 border ${
                  isActive
                    ? 'bg-[#111925] text-[#62CBE8] border-[#62CBE8]'
                    : 'bg-[#161F2D] text-[#A0AEC0] border-[#263246] hover:text-[#F1F5F9] hover:bg-[#1E293B]'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            )
          })}
        </div>

        {/* Screen Preview Frame */}
        <div className="bg-[#111925] border border-[#263246] rounded-2xl overflow-hidden shadow-xl">
          {/* Mock Browser Header */}
          <div className="bg-[#090D16] px-4 py-3 border-b border-[#263246] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-[#E47777]" />
              <span className="w-3 h-3 rounded-full bg-[#E5B85C]" />
              <span className="w-3 h-3 rounded-full bg-[#38B982]" />
              <span className="ml-3 text-xs font-mono text-[#A0AEC0]">
                https://yuktiops.dev/workspace/{activeTab}
              </span>
            </div>
            <button
              onClick={onLaunchWorkspace}
              className="px-3 py-1 bg-[#62CBE8] hover:bg-[#79D6EE] text-[#07131C] font-semibold text-xs font-mono rounded flex items-center gap-1.5 transition-colors"
            >
              <span>Open Workspace</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Screen Content Preview */}
          <div className="p-6 sm:p-8 bg-[#111925]">
            <AnimatePresence mode="wait">
              {activeTab === 'command' && (
                <motion.div
                  key="command"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="space-y-6"
                >
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="p-4 bg-[#161F2D] rounded-xl border border-[#263246]">
                      <div className="text-xs font-mono text-[#A0AEC0] mb-1">SPRINT VELOCITY</div>
                      <div className="text-2xl font-bold text-[#F1F5F9]">33% Completed</div>
                      <div className="text-xs text-[#77869B] font-mono mt-1">2 of 6 tasks shipped</div>
                    </div>
                    <div className="p-4 bg-[#161F2D] rounded-xl border border-[#263246]">
                      <div className="text-xs font-mono text-[#A0AEC0] mb-1">ACTIVE BLOCKERS</div>
                      <div className="text-2xl font-bold text-[#E47777]">1 P0 Risk</div>
                      <div className="text-xs text-[#77869B] font-mono mt-1">Auth API integration pending</div>
                    </div>
                    <div className="p-4 bg-[#161F2D] rounded-xl border border-[#263246]">
                      <div className="text-xs font-mono text-[#A0AEC0] mb-1">DECISIONS PENDING</div>
                      <div className="text-2xl font-bold text-[#E5B85C]">1 Leader Flag</div>
                      <div className="text-xs text-[#77869B] font-mono mt-1">Quoted chat evidence ready</div>
                    </div>
                  </div>
                </motion.div>
              )}

              {activeTab === 'chat' && (
                <motion.div
                  key="chat"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="space-y-4"
                >
                  <div className="p-4 bg-[#161F2D] rounded-xl border border-[#263246] flex items-start gap-3">
                    <div className="w-9 h-9 rounded-full bg-[#111925] text-[#62CBE8] font-bold flex items-center justify-center shrink-0 border border-[#263246]">
                      PS
                    </div>
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-bold text-[#F1F5F9] text-sm">Priya Sharma</span>
                        <span className="text-[10px] font-mono text-[#62CBE8] bg-[#090D16] px-1.5 py-0.5 rounded border border-[#263246]">
                          Frontend
                        </span>
                        <span className="text-xs text-[#77869B] font-mono">10:42 AM</span>
                      </div>
                      <p className="text-sm font-mono text-[#F1F5F9] bg-[#090D16] p-3 rounded-lg border border-[#263246]">
                        &quot;Login UI page done, but backend auth API nahi mila yet.&quot;
                      </p>
                      <div className="mt-2 inline-flex items-center gap-1.5 text-xs text-[#E5B85C] bg-[#E5B85C]/10 border border-[#E5B85C]/30 px-2.5 py-1 rounded-md font-mono">
                        <AlertTriangle className="w-3.5 h-3.5" />
                        <span>AI Detected Blocker: Mapped to YUKTI-104</span>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}

              {activeTab === 'tasks' && (
                <motion.div
                  key="tasks"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="grid grid-cols-1 sm:grid-cols-3 gap-4"
                >
                  <div className="p-4 bg-[#161F2D] rounded-xl border border-[#263246]">
                    <span className="text-xs font-mono font-bold text-[#A0AEC0] block mb-3">IN PROGRESS</span>
                    <div className="p-3 bg-[#090D16] rounded-lg border border-[#263246] text-xs space-y-1">
                      <span className="font-mono text-[#62CBE8] font-bold">YUKTI-103</span>
                      <div className="font-semibold text-[#F1F5F9]">Discord Shell UI</div>
                      <span className="text-[#77869B] font-mono text-[10px]">Priya · P1</span>
                    </div>
                  </div>
                  <div className="p-4 bg-[#161F2D] rounded-xl border border-[#E47777]/30">
                    <span className="text-xs font-mono font-bold text-[#E47777] block mb-3">BLOCKED / WAITING</span>
                    <div className="p-3 bg-[#090D16] rounded-lg border border-[#E47777]/30 text-xs space-y-1">
                      <span className="font-mono text-[#E47777] font-bold">YUKTI-104</span>
                      <div className="font-semibold text-[#F1F5F9]">Auth API Integration</div>
                      <span className="text-[#E47777] font-mono text-[10px] block">Waiting on: Backend Auth</span>
                    </div>
                  </div>
                  <div className="p-4 bg-[#161F2D] rounded-xl border border-[#38B982]/30">
                    <span className="text-xs font-mono font-bold text-[#38B982] block mb-3">DONE &amp; SHIPPED</span>
                    <div className="p-3 bg-[#090D16] rounded-lg border border-[#38B982]/30 text-xs space-y-1">
                      <span className="font-mono text-[#38B982] font-bold">YUKTI-102</span>
                      <div className="font-semibold text-[#F1F5F9]">GitHub Webhooks</div>
                      <span className="text-[#38B982] font-mono text-[10px]">PR #11 Merged</span>
                    </div>
                  </div>
                </motion.div>
              )}

              {activeTab === 'git' && (
                <motion.div
                  key="git"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="space-y-3 font-mono text-xs"
                >
                  <div className="p-3 bg-[#161F2D] rounded-lg border border-[#263246] flex items-center justify-between">
                    <div>
                      <span className="text-[#38B982] font-bold">[PR #14: OPEN] </span>
                      <span className="text-[#F1F5F9]">feat: login page &amp; auth flow</span>
                      <span className="text-[#77869B] block text-[11px]">Mapped to task YUKTI-104</span>
                    </div>
                    <span className="px-2 py-0.5 rounded bg-[#090D16] text-[#A0AEC0]">15m ago</span>
                  </div>
                  <div className="p-3 bg-[#161F2D] rounded-lg border border-[#263246] flex items-center justify-between">
                    <div>
                      <span className="text-[#62CBE8] font-bold">[PR #11: MERGED] </span>
                      <span className="text-[#F1F5F9]">feat: webhook signature verification</span>
                      <span className="text-[#77869B] block text-[11px]">Verified Code Evidence</span>
                    </div>
                    <span className="px-2 py-0.5 rounded bg-[#090D16] text-[#A0AEC0]">1h ago</span>
                  </div>
                </motion.div>
              )}

              {activeTab === 'inbox' && (
                <motion.div
                  key="inbox"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="p-5 bg-[#161F2D] border border-[#E5B85C]/40 rounded-xl space-y-3"
                >
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-[#E5B85C] font-bold flex items-center gap-1.5">
                      <ShieldCheck className="w-4 h-4" />
                      LEAD DECISION REQUIRED · YUKTI-104
                    </span>
                    <span className="text-[#62CBE8] font-bold">Assessment Confidence: 94%</span>
                  </div>
                  <p className="text-sm text-[#A0AEC0]">
                    Frontend integration blocked pending backend authentication credentials.
                  </p>
                  <div className="p-3 bg-[#090D16] rounded-lg border border-[#263246] text-xs font-mono text-[#62CBE8]">
                    Source Evidence: &quot;Login UI page done, but backend auth API nahi mila yet.&quot;
                  </div>
                  <div className="pt-2 flex justify-end gap-3 text-xs font-mono">
                    <button className="px-3 py-1.5 rounded bg-[#090D16] text-[#E47777] border border-[#E47777]/30 hover:bg-[#E47777]/10 transition-colors">
                      [Reject]
                    </button>
                    <button 
                      onClick={onLaunchWorkspace}
                      className="px-4 py-1.5 rounded bg-[#38B982] hover:bg-[#38B982]/90 text-[#07131C] font-semibold transition-colors"
                    >
                      [Approve &amp; Synchronize Task]
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </section>
  )
}

export default ScreensShowcase
