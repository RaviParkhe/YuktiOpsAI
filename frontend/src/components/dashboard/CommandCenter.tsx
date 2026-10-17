import React from 'react'
import { 
  AlertTriangle, 
  GitPullRequest, 
  ArrowRight, 
  TrendingUp, 
  Users, 
  AlertCircle,
  Kanban,
  Plus,
  GitCommit,
  ChevronRight
} from 'lucide-react'
import type { Task, ProjectStats, AIProposal, GitEvent } from '../../types/models'
import type { User } from '../../types/auth'

interface CommandCenterProps {
  currentUser: User
  stats: ProjectStats
  tasks: Task[]
  proposals: AIProposal[]
  gitEvents: GitEvent[]
  onNavigateToInbox: () => void
  onNavigateToTasks: () => void
  onNavigateToGit: () => void
  onOpenCreateTaskModal?: () => void
}

export const CommandCenter: React.FC<CommandCenterProps> = ({
  currentUser,
  stats,
  tasks,
  proposals,
  gitEvents,
  onNavigateToInbox,
  onNavigateToTasks,
  onNavigateToGit,
  onOpenCreateTaskModal,
}) => {
  const isAdmin = currentUser.role === 'ADMIN'
  const blockedTasks = tasks.filter((t) => t.status === 'BLOCKED')
  const inProgressTasks = tasks.filter((t) => t.status === 'IN_PROGRESS')
  const completedTasks = tasks.filter((t) => t.status === 'DONE')
  const pendingProposals = proposals.filter((p) => p.status === 'PENDING')

  // Calculated completion rate; null if no tasks registered
  const completionPercentage = tasks.length > 0 
    ? Math.round((completedTasks.length / tasks.length) * 100) 
    : null

  // Filter for developer view: only tasks assigned to the current user
  const myTasks = tasks.filter((t) => t.assignee.id === currentUser.id)

  // Unique genuine assignees
  const uniqueAssignees = Array.from(new Set(tasks.map((t) => t.assignee.name))).filter(Boolean)

  return (
    <div className="h-full overflow-y-auto p-5 sm:p-7 bg-[#090D16]">
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* A. REFINED PAGE HEADER: Display font heading with metadata */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-[#263246]/60">
          <div>
            <h1 className="text-xl sm:text-2xl font-normal text-[#F1F5F9] tracking-wide font-display">
              Command Center
            </h1>
            <div className="flex flex-wrap items-center gap-2 mt-1 text-xs text-[#A0AEC0] font-sans">
              <span className="flex items-center gap-1.5 text-[#F1F5F9]">
                <span className="w-1.5 h-1.5 rounded-full bg-[#38B982]" />
                <span>{stats.activeSprint || 'Sprint 1'}</span>
              </span>
              <span className="text-[#77869B]">·</span>
              <span className="text-[#77869B]">
                {stats.repoConnected && stats.repoName ? stats.repoName : 'Repository not linked'}
              </span>
              <span className="text-[#77869B]">·</span>
              <span className="text-[#77869B]">
                Role: <span className={isAdmin ? 'text-[#62CBE8]' : 'text-[#38B982]'}>{isAdmin ? 'Project Lead' : 'Developer'}</span>
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            {onOpenCreateTaskModal && (
              <button
                onClick={onOpenCreateTaskModal}
                className="px-3.5 py-1.5 bg-[#62CBE8] hover:bg-[#79D6EE] text-[#07131C] text-xs font-semibold rounded-lg inline-flex items-center gap-1.5 transition-colors shadow-xs font-sans"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Create Task</span>
              </button>
            )}
          </div>
        </div>

        {/* HIGH-PRIORITY LEAD REVIEW BANNER (Only when genuine proposals exist) */}
        {isAdmin && pendingProposals.length > 0 && (
          <div className="bg-[#111925] border border-[#E5B85C]/40 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3.5 shadow-sm">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-[#E5B85C]/10 text-[#E5B85C] rounded-lg shrink-0 mt-0.5 border border-[#E5B85C]/20">
                <AlertTriangle className="w-4 h-4" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-[#F1F5F9] text-xs sm:text-sm font-sans">
                    {pendingProposals.length} Blocker Proposal Awaiting Authorization
                  </span>
                  <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-[#E47777]/20 text-[#E47777] border border-[#E47777]/30 font-bold">
                    P0
                  </span>
                </div>
                <p className="text-xs text-[#A0AEC0] mt-0.5 font-sans">
                  AI extracted potential blocker on <strong className="text-[#F1F5F9] font-mono">{pendingProposals[0].taskId}</strong> from channel discussion.
                </p>
              </div>
            </div>

            <button
              onClick={onNavigateToInbox}
              className="px-3.5 py-1.5 bg-[#E5B85C] hover:bg-[#d4a74e] text-[#090D16] font-semibold text-xs rounded-lg flex items-center gap-2 shrink-0 transition-colors font-sans"
            >
              <span>Review Proposal</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* C. OPERATIONAL METRICS STRIP: Unified, restrained 4-segment stats bar */}
        <div className="bg-[#111925] border border-[#263246] rounded-xl overflow-hidden shadow-xs">
          <div className="grid grid-cols-2 lg:grid-cols-4 divide-y lg:divide-y-0 lg:divide-x divide-[#263246]/60">
            {/* Metric 1: Sprint Progress */}
            <div className="p-4 sm:p-5">
              <div className="flex items-center justify-between text-xs text-[#77869B] font-medium font-sans mb-1.5">
                <span>Sprint Progress</span>
                <TrendingUp className="w-3.5 h-3.5 text-[#38B982]" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-[#F1F5F9] font-sans">
                  {completionPercentage !== null ? `${completionPercentage}%` : '—'}
                </span>
                <span className="text-xs text-[#A0AEC0] font-sans">
                  {tasks.length > 0 ? `${completedTasks.length}/${tasks.length} closed` : 'No tasks recorded'}
                </span>
              </div>
              {completionPercentage !== null ? (
                <div className="w-full bg-[#161F2D] h-1 rounded-full overflow-hidden mt-2.5">
                  <div
                    className="bg-[#38B982] h-full transition-all duration-300 rounded-full"
                    style={{ width: `${completionPercentage}%` }}
                  />
                </div>
              ) : (
                <div className="text-[11px] text-[#77869B] font-sans mt-2">
                  Sprint unstarted
                </div>
              )}
            </div>

            {/* Metric 2: Active Blockers */}
            <div className="p-4 sm:p-5">
              <div className="flex items-center justify-between text-xs text-[#77869B] font-medium font-sans mb-1.5">
                <span>Active Blockers</span>
                <AlertCircle className={`w-3.5 h-3.5 ${blockedTasks.length > 0 ? 'text-[#E47777]' : 'text-[#38B982]'}`} />
              </div>
              <div className="flex items-baseline gap-2">
                <span className={`text-2xl font-bold font-sans ${blockedTasks.length > 0 ? 'text-[#E47777]' : 'text-[#F1F5F9]'}`}>
                  {blockedTasks.length}
                </span>
                <span className="text-xs text-[#A0AEC0] font-sans flex items-center gap-1.5">
                  <span className={`w-1.5 h-1.5 rounded-full ${blockedTasks.length > 0 ? 'bg-[#E47777] animate-pulse' : 'bg-[#38B982]'}`} />
                  <span>{blockedTasks.length > 0 ? 'Action required' : 'Zero blockers'}</span>
                </span>
              </div>
              <div className="text-[11px] text-[#77869B] font-sans mt-2">
                {blockedTasks.length > 0 ? `${blockedTasks.length} critical path stoppage` : 'Pipeline running clear'}
              </div>
            </div>

            {/* Metric 3: Work in Flight */}
            <div className="p-4 sm:p-5">
              <div className="flex items-center justify-between text-xs text-[#77869B] font-medium font-sans mb-1.5">
                <span>Work in Flight</span>
                <Kanban className="w-3.5 h-3.5 text-[#62CBE8]" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-[#F1F5F9] font-sans">
                  {inProgressTasks.length}
                </span>
                <span className="text-xs text-[#A0AEC0] font-sans">
                  {inProgressTasks.length === 1 ? '1 task executing' : `${inProgressTasks.length} tasks executing`}
                </span>
              </div>
              <div className="text-[11px] text-[#77869B] font-sans mt-2">
                {tasks.length > 0 ? `${tasks.filter(t => t.status === 'BACKLOG').length} pending in backlog` : 'Backlog unpopulated'}
              </div>
            </div>

            {/* Metric 4: Repository Integration */}
            <div className="p-4 sm:p-5">
              <div className="flex items-center justify-between text-xs text-[#77869B] font-medium font-sans mb-1.5">
                <span>Git Integration</span>
                <GitPullRequest className={`w-3.5 h-3.5 ${stats.repoConnected ? 'text-[#38B982]' : 'text-[#77869B]'}`} />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-base font-semibold text-[#F1F5F9] font-sans truncate">
                  {stats.repoConnected && stats.repoName ? stats.repoName : 'Not Configured'}
                </span>
              </div>
              <div className="flex items-center gap-1.5 mt-2 text-xs text-[#A0AEC0] font-sans">
                <span className={`w-1.5 h-1.5 rounded-full ${stats.repoConnected ? 'bg-[#38B982]' : 'bg-[#77869B]'}`} />
                <span>{stats.repoConnected ? 'Webhooks active' : 'Disconnected'}</span>
              </div>
            </div>
          </div>
        </div>

        {/* D. ASYMMETRIC 2-COLUMN WORKSPACE: Spacious main workstream + Focused right panel */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          
          {/* LEFT DOMINANT COLUMN (8 Cols): Active Sprint Stream + Blocker Radar + Code Activity */}
          <div className="lg:col-span-8 space-y-6">
            
            {/* 1. SPRINT WORKSTREAM & BLOCKER RADAR */}
            <div className="bg-[#111925] border border-[#263246] rounded-xl overflow-hidden shadow-xs">
              <div className="px-5 py-3.5 border-b border-[#263246] flex items-center justify-between bg-[#111925]">
                <div className="flex items-center gap-2">
                  <h2 className="text-sm font-semibold text-[#F1F5F9] font-sans">
                    Sprint Workstream
                  </h2>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-[#161F2D] text-[#A0AEC0] border border-[#263246] font-sans">
                    {tasks.length} {tasks.length === 1 ? 'task' : 'tasks'}
                  </span>
                </div>

                {tasks.length > 0 && (
                  <button
                    onClick={onNavigateToTasks}
                    className="text-xs text-[#62CBE8] hover:text-[#79D6EE] font-medium inline-flex items-center gap-1 font-sans transition-colors"
                  >
                    <span>View Task Board</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>

              {/* Task Content Area */}
              <div className="p-5">
                {/* Case 1: Empty state (compact, integrated, non-dominating) */}
                {tasks.length === 0 && (
                  <div className="py-7 px-5 text-center border border-dashed border-[#263246] rounded-xl bg-[#090D16]/40">
                    <div className="w-9 h-9 rounded-lg bg-[#161F2D] border border-[#263246] flex items-center justify-center text-[#62CBE8] mx-auto mb-2.5">
                      <Kanban className="w-4 h-4" />
                    </div>
                    <h3 className="text-sm font-semibold text-[#F1F5F9] font-sans">No tasks in current sprint</h3>
                    <p className="text-xs text-[#77869B] max-w-sm mx-auto mt-1 font-sans">
                      Add engineering items with acceptance criteria to monitor dependencies, blocker evidence, and team progress.
                    </p>
                    {onOpenCreateTaskModal && (
                      <button
                        onClick={onOpenCreateTaskModal}
                        className="mt-3.5 px-3 py-1.5 bg-[#161F2D] hover:bg-[#1E293B] text-[#62CBE8] hover:text-[#79D6EE] border border-[#263246] text-xs font-medium rounded-lg inline-flex items-center gap-1.5 transition-colors font-sans"
                      >
                        <Plus className="w-3.5 h-3.5" />
                        <span>Create First Task</span>
                      </button>
                    )}
                  </div>
                )}

                {/* Case 2: Tasks exist, with confirmed blockers */}
                {blockedTasks.length > 0 && (
                  <div className="space-y-3 mb-4">
                    <div className="flex items-center gap-2 text-xs font-semibold text-[#E47777] font-sans">
                      <AlertTriangle className="w-3.5 h-3.5" />
                      <span>Confirmed Blockers ({blockedTasks.length})</span>
                    </div>

                    {blockedTasks.map((t) => (
                      <div
                        key={t.id}
                        className="p-3.5 bg-[#161F2D] border border-[#E47777]/40 rounded-lg space-y-2.5"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-mono font-bold text-[#E47777] bg-[#E47777]/15 px-2 py-0.5 rounded border border-[#E47777]/30">
                              {t.id}
                            </span>
                            <span className="text-xs font-semibold text-[#F1F5F9] font-sans">{t.title}</span>
                          </div>
                          <span className="text-[10px] font-mono bg-[#E47777] text-[#090D16] px-1.5 py-0.5 rounded font-bold">
                            {t.priority}
                          </span>
                        </div>

                        {t.waitingOn && (
                          <div className="text-xs text-[#E47777] font-sans flex items-center gap-1.5">
                            <span className="font-medium text-[#77869B]">Waiting on:</span>
                            <span>{t.waitingOn}</span>
                          </div>
                        )}

                        {t.evidenceSnippet && (
                          <div className="text-xs font-mono bg-[#090D16] p-2.5 rounded text-[#E5B85C] border border-[#263246] leading-relaxed">
                            Quoted Evidence: &quot;{t.evidenceSnippet}&quot;
                          </div>
                        )}

                        <div className="flex items-center justify-between text-[11px] text-[#77869B] pt-2 border-t border-[#263246]/60 font-sans">
                          <span>Assignee: <strong className="text-[#F1F5F9]">{t.assignee.name}</strong></span>
                          <span className="font-mono text-[10px]">{t.updatedAt}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                  <div className="space-y-2">
                    {blockedTasks.length > 0 && (
                      <div className="text-xs font-semibold text-[#A0AEC0] font-sans pt-2">
                        Active Engineering Pipeline
                      </div>
                    )}
                    <div className="border border-[#263246] rounded-lg bg-[#090D16]/50 divide-y divide-[#263246]/60 overflow-hidden">
                      {tasks.filter(t => t.status !== 'BLOCKED').slice(0, 4).map((t) => (
                        <div
                          key={t.id}
                          className="px-3.5 py-2.5 hover:bg-[#161F2D]/50 flex items-center justify-between gap-3 transition-colors"
                        >
                          <div className="flex items-center gap-2.5 min-w-0">
                            <span className="text-xs font-mono font-medium text-[#62CBE8] shrink-0">
                              {t.id}
                            </span>
                            <span className="text-xs text-[#F1F5F9] font-medium truncate font-sans">
                              {t.title}
                            </span>
                          </div>

                          <div className="flex items-center gap-3 shrink-0">
                            <span className="text-xs text-[#77869B] hidden sm:inline font-sans">
                              {t.assignee.name}
                            </span>
                            <span className={`text-[10px] font-sans px-2 py-0.5 rounded font-medium ${
                              t.status === 'DONE'
                                ? 'bg-[#38B982]/15 text-[#38B982]'
                                : t.status === 'IN_PROGRESS'
                                ? 'bg-[#62CBE8]/15 text-[#62CBE8]'
                                : 'bg-[#161F2D] text-[#A0AEC0]'
                            }`}>
                              {t.status}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
              </div>
            </div>

            {/* 2. RECENT CODE ACTIVITY STREAM */}
            <div className="bg-[#111925] border border-[#263246] rounded-xl overflow-hidden shadow-xs">
              <div className="px-5 py-3.5 border-b border-[#263246] flex items-center justify-between bg-[#111925]">
                <div className="flex items-center gap-2">
                  <h2 className="text-sm font-semibold text-[#F1F5F9] font-sans">
                    Code Activity Stream
                  </h2>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-[#161F2D] text-[#A0AEC0] border border-[#263246] font-sans">
                    {gitEvents.length} events
                  </span>
                </div>

                <button
                  onClick={onNavigateToGit}
                  className="text-xs text-[#62CBE8] hover:text-[#79D6EE] font-medium inline-flex items-center gap-1 font-sans transition-colors"
                >
                  <span>All Git Feeds</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>

              <div className="p-5">
                {gitEvents.length === 0 ? (
                  <div className="p-5 text-center text-xs text-[#77869B] font-sans border border-[#263246]/60 rounded-lg bg-[#090D16]/30">
                    <p>No repository commits or pull requests recorded yet.</p>
                    <button
                      onClick={onNavigateToGit}
                      className="text-xs text-[#62CBE8] hover:underline font-sans mt-1.5 inline-block"
                    >
                      Dispatch a test webhook from Git Activity →
                    </button>
                  </div>
                ) : (
                  <div className="divide-y divide-[#263246]/60">
                    {gitEvents.slice(0, 4).map((event) => (
                      <div
                        key={event.id}
                        className="py-3 first:pt-0 last:pb-0 flex items-center justify-between gap-3 text-xs"
                      >
                        <div className="flex items-center gap-3 min-w-0">
                          <span className="w-6 h-6 rounded-md bg-[#161F2D] border border-[#263246] flex items-center justify-center text-[#38B982] shrink-0">
                            {event.type === 'PR' ? (
                              <GitPullRequest className="w-3.5 h-3.5" />
                            ) : (
                              <GitCommit className="w-3.5 h-3.5" />
                            )}
                          </span>
                          <div className="min-w-0">
                            <div className="font-medium text-[#F1F5F9] truncate font-sans">
                              {event.title}
                            </div>
                            <div className="text-[11px] text-[#77869B] font-sans">
                              by <strong className="text-[#A0AEC0] font-mono">@{event.author}</strong> in <span className="font-mono">{event.branch || 'main'}</span>
                            </div>
                          </div>
                        </div>

                        <span className="text-[#77869B] font-mono text-[10px] shrink-0">
                          {event.timestamp}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

          </div>

          {/* RIGHT CONTEXT COLUMN (4 Cols): Capacity, Queue Status, or Assigned Tasks */}
          <div className="lg:col-span-4 space-y-6">
            
            {/* 1. DECISION QUEUE STATUS (Admin context) */}
            {isAdmin && (
              <div className="bg-[#111925] border border-[#263246] rounded-xl p-4 shadow-xs">
                <div className="flex items-center justify-between mb-2.5">
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-[#A0AEC0] font-sans">
                    Decision Inbox
                  </h3>
                  <button
                    onClick={onNavigateToInbox}
                    className="text-xs text-[#62CBE8] hover:underline font-sans"
                  >
                    Open Queue →
                  </button>
                </div>

                {pendingProposals.length === 0 ? (
                  <div className="flex items-center gap-2.5 py-1">
                    <span className="w-2 h-2 rounded-full bg-[#38B982] shrink-0" />
                    <div>
                      <p className="text-xs font-medium text-[#F1F5F9] font-sans">Queue Clear</p>
                      <p className="text-[11px] text-[#77869B] font-sans">Zero blocker proposals awaiting lead review</p>
                    </div>
                  </div>
                ) : (
                  <div className="p-2.5 bg-[#E5B85C]/10 border border-[#E5B85C]/30 rounded-lg">
                    <div className="text-xs font-semibold text-[#E5B85C] font-sans">
                      {pendingProposals.length} item(s) pending review
                    </div>
                    <p className="text-[11px] text-[#A0AEC0] mt-0.5 font-sans">
                      Authorize blocker status for {pendingProposals[0].taskId}
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* 2. TEAM WORKLOAD ALLOCATION (Admin) OR MY ASSIGNED WORK (Developer) */}
            <div className="bg-[#111925] border border-[#263246] rounded-xl p-5 shadow-xs">
              {isAdmin ? (
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <h3 className="text-sm font-semibold text-[#F1F5F9] font-sans">
                      Team Capacity
                    </h3>
                    <span className="text-[10px] font-sans text-[#77869B] px-1.5 py-0.5 rounded bg-[#161F2D] border border-[#263246]">
                      Admin View
                    </span>
                  </div>

                  <p className="text-xs text-[#77869B] font-sans mb-4">
                    Active task distribution across current sprint assignees.
                  </p>

                  {uniqueAssignees.length === 0 ? (
                    <div className="p-5 text-center text-xs text-[#77869B] font-sans border border-[#263246]/60 rounded-lg bg-[#090D16]/30">
                      <Users className="w-5 h-5 text-[#77869B] mx-auto mb-1.5" />
                      <p className="text-xs text-[#A0AEC0] font-sans">No task assignees recorded</p>
                      <p className="text-[11px] text-[#77869B] mt-0.5 font-sans">
                        Workload calculates as tasks are assigned to developers.
                      </p>
                    </div>
                  ) : (
                    <div className="border border-[#263246] rounded-lg bg-[#090D16]/40 divide-y divide-[#263246]/60 overflow-hidden">
                      {uniqueAssignees.map((devName) => {
                        const devTasks = tasks.filter((t) => t.assignee.name === devName)
                        const isDevBlocked = devTasks.some((t) => t.status === 'BLOCKED')
                        const loadPct = tasks.length > 0 ? Math.round((devTasks.length / tasks.length) * 100) : 0

                        return (
                          <div
                            key={devName}
                            className="p-3 hover:bg-[#161F2D]/40 space-y-2 transition-colors"
                          >
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                <span className="text-xs font-semibold text-[#F1F5F9] font-sans">{devName}</span>
                                {isDevBlocked && (
                                  <span className="text-[10px] px-1.5 py-0.2 rounded bg-[#E47777]/20 text-[#E47777] font-sans font-medium">
                                    BLOCKED
                                  </span>
                                )}
                              </div>
                              <span className="text-xs font-sans text-[#A0AEC0]">
                                {devTasks.length} {devTasks.length === 1 ? 'task' : 'tasks'}
                              </span>
                            </div>

                            <div className="w-full bg-[#111925] h-1.5 rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full transition-all duration-300 ${
                                  isDevBlocked ? 'bg-[#E47777]' : 'bg-[#62CBE8]'
                                }`}
                                style={{ width: `${Math.min(loadPct, 100)}%` }}
                              />
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>
              ) : (
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <h3 className="text-sm font-semibold text-[#F1F5F9] font-sans">
                      My Assigned Work
                    </h3>
                    <span className="text-[10px] font-sans text-[#38B982] px-1.5 py-0.5 rounded bg-[#161F2D] border border-[#38B982]/30">
                      Developer
                    </span>
                  </div>

                  <p className="text-xs text-[#77869B] font-sans mb-4">
                    Items assigned to your profile in this sprint.
                  </p>

                  <div className="border border-[#263246] rounded-lg bg-[#090D16]/40 divide-y divide-[#263246]/60 overflow-hidden">
                    {myTasks.length === 0 ? (
                      <div className="p-4 text-center text-xs text-[#77869B] font-sans">
                        No active sprint tasks assigned to you.
                      </div>
                    ) : (
                      myTasks.map((t) => (
                        <div
                          key={t.id}
                          className="p-3 hover:bg-[#161F2D]/40 space-y-1 transition-colors"
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-mono text-xs text-[#62CBE8] font-semibold">{t.id}</span>
                            <span className="text-[10px] font-sans font-medium px-2 py-0.5 rounded bg-[#161F2D] text-[#A0AEC0]">
                              {t.status}
                            </span>
                          </div>
                          <div className="text-xs font-medium text-[#F1F5F9] font-sans">{t.title}</div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>

          </div>

        </div>

      </div>
    </div>
  )
}

export default CommandCenter
