import React, { useState } from 'react'
import { 
  Activity, 
  Kanban, 
  GitBranch, 
  ShieldCheck, 
  Hash, 
  Users, 
  LogOut, 
  Lock, 
  AlertTriangle, 
  ChevronDown, 
  Plus,
  Zap,
  Clock,
  Settings,
  PanelRightClose,
  PanelRight,
  Menu,
  X
} from 'lucide-react'
import { YuktiMark, YuktiWordmark } from '../ui/YuktiLogo'
import ParticleBackground from '../ui/particle-background'
import type { User } from '../../types/auth'
import type { Task } from '../../types/models'

export type ActiveView = 
  | 'COMMAND_CENTER' 
  | 'TASK_BOARD' 
  | 'GIT_ACTIVITY' 
  | 'ADMIN_INBOX' 
  | 'CHAT'
  | 'INTEGRATIONS'
  | 'AUDIT_LOG'
  | 'SETTINGS'

interface WorkspaceShellProps {
  currentUser: User
  teamMembers?: User[]
  activeView: ActiveView
  activeChannel: string
  pendingProposalsCount: number
  tasks: Task[]
  onSelectView: (view: ActiveView) => void
  onSelectChannel: (channelId: string) => void
  onToggleRole: () => void
  onLogout: () => void
  children: React.ReactNode
}

export const WorkspaceShell: React.FC<WorkspaceShellProps> = ({
  currentUser,
  teamMembers,
  activeView,
  activeChannel,
  pendingProposalsCount,
  tasks,
  onSelectView,
  onSelectChannel,
  onToggleRole,
  onLogout,
  children,
}) => {
  const [isRightSidebarOpen, setIsRightSidebarOpen] = useState(true)
  const [isMobileNavOpen, setIsMobileNavOpen] = useState(false)
  const isAdmin = currentUser.role === 'ADMIN'
  const blockedTasks = tasks.filter((t) => t.status === 'BLOCKED')

  const CHANNELS = [
    { id: 'general', name: 'general' },
    { id: 'frontend', name: 'frontend' },
    { id: 'backend', name: 'backend' },
    { id: 'blockers', name: 'blockers' },
  ]

  const handleNavClick = (view: ActiveView) => {
    onSelectView(view)
    setIsMobileNavOpen(false)
  }

  const handleChannelClick = (channelId: string) => {
    onSelectChannel(channelId)
    onSelectView('CHAT')
    setIsMobileNavOpen(false)
  }

  return (
    <div className="h-screen w-screen flex flex-col lg:flex-row bg-[#090D16] text-[#F1F5F9] overflow-hidden select-none font-sans">
      {/* MOBILE TOP BAR (visible only on < lg screens) */}
      <div className="lg:hidden h-14 bg-[#111925] border-b border-[#263246] px-4 flex items-center justify-between z-30 shrink-0">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsMobileNavOpen(!isMobileNavOpen)}
            className="p-1.5 rounded-lg bg-[#161F2D] border border-[#263246] text-[#A0AEC0] hover:text-[#F1F5F9]"
            aria-label="Toggle Navigation Menu"
          >
            {isMobileNavOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
          <YuktiWordmark size="sm" />
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsRightSidebarOpen(!isRightSidebarOpen)}
            className={`p-1.5 rounded-lg border text-xs font-sans font-medium flex items-center gap-1.5 transition-colors ${
              isRightSidebarOpen 
                ? 'bg-[#161F2D] text-[#62CBE8] border-[#62CBE8]/40' 
                : 'bg-[#111925] text-[#A0AEC0] border-[#263246]'
            }`}
            title="Toggle Active Context"
          >
            <Users className="w-4 h-4" />
            <span className="hidden sm:inline">Context</span>
          </button>

          <button
            onClick={onToggleRole}
            className="px-2 py-1 rounded bg-[#161F2D] text-[#A0AEC0] hover:text-[#F1F5F9] text-xs font-sans font-medium border border-[#263246]"
            title="Toggle user role (Admin / Developer)"
          >
            {currentUser.role === 'ADMIN' ? 'Admin' : 'Dev'}
          </button>
        </div>
      </div>

      {/* MOBILE BACKDROP */}
      {isMobileNavOpen && (
        <div 
          onClick={() => setIsMobileNavOpen(false)}
          className="fixed inset-0 bg-black/60 backdrop-blur-xs z-30 lg:hidden"
        />
      )}

      {/* NAVIGATION WRAPPER (Left Rail + Project Sidebar) */}
      <div className={`fixed inset-y-0 left-0 z-40 flex transform transition-transform duration-200 ease-in-out lg:relative lg:translate-x-0 ${
        isMobileNavOpen ? 'translate-x-0' : '-translate-x-full'
      }`}>
        {/* 1. LEFT RAIL: Workspace & Repo Selector (56px wide) */}
        <div className="w-14 bg-[#090D16] flex flex-col items-center py-3.5 gap-2.5 shrink-0 border-r border-[#263246] z-20">
          {/* YuktiOps Home Logo */}
          <div 
            onClick={() => handleNavClick('COMMAND_CENTER')}
            className="group relative flex items-center justify-center cursor-pointer"
            title="युक्तिOps Command Center"
          >
            <div className="w-9 h-9 bg-[#111925] hover:bg-[#161F2D] border border-[#263246] hover:border-[#62CBE8]/50 rounded-lg transition-all flex items-center justify-center text-[#62CBE8]">
              <YuktiMark size={18} />
            </div>
          </div>

          <div className="w-5 h-[1px] bg-[#263246] rounded" />

          {/* Connected Repository Icon */}
          <div 
            onClick={() => handleNavClick('GIT_ACTIVITY')}
            className="group relative flex items-center justify-center cursor-pointer"
            title="Connected GitHub: yuktiops/workspace"
          >
            <div className={`w-9 h-9 bg-[#111925] hover:bg-[#161F2D] rounded-lg transition-all flex items-center justify-center text-[#F1F5F9] border border-[#263246] ${
              activeView === 'GIT_ACTIVITY' ? 'border-[#62CBE8] bg-[#161F2D]' : ''
            }`}>
              <GitBranch className="w-3.5 h-3.5 text-[#38B982]" />
            </div>
            <span className="absolute bottom-0 right-1 w-2 h-2 bg-[#38B982] rounded-full border-2 border-[#090D16]" />
          </div>

          {/* Add / Switch Project */}
          <div 
            className="w-9 h-9 bg-[#111925] hover:bg-[#161F2D] text-[#A0AEC0] hover:text-[#62CBE8] rounded-lg transition-all flex items-center justify-center cursor-pointer border border-[#263246]"
            title="Add or Switch Workspace"
          >
            <Plus className="w-3.5 h-3.5" />
          </div>

          <div className="mt-auto flex flex-col items-center gap-2">
            <button
              onClick={() => handleNavClick('SETTINGS')}
              className={`w-9 h-9 rounded-lg flex items-center justify-center transition-colors border ${
                activeView === 'SETTINGS'
                  ? 'bg-[#161F2D] text-[#62CBE8] border-[#62CBE8]'
                  : 'bg-[#111925] text-[#A0AEC0] hover:text-[#F1F5F9] border-[#263246]'
              }`}
              title="Workspace Settings"
            >
              <Settings className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* 2. SECOND SIDEBAR: Project Views & Channels (208px wide) */}
        <div className="w-52 bg-[#111925] flex flex-col shrink-0 border-r border-[#263246] z-10">
          {/* Project Header */}
          <div className="h-14 px-3 border-b border-[#263246] flex items-center justify-between shadow-xs">
            <div className="flex items-center gap-2">
              <YuktiWordmark size="sm" />
              <span className="text-[10px] font-sans font-medium px-1.5 py-0.5 rounded bg-[#090D16] text-[#62CBE8] border border-[#263246]">
                Sprint 1
              </span>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-[#77869B]" />
          </div>

          {/* Navigation Section */}
          <div className="flex-1 overflow-y-auto px-2.5 py-3 space-y-5">
            {/* Workspace Views */}
            <div>
              <div className="px-2 mb-1.5 text-[11px] font-sans uppercase tracking-wider text-[#77869B] font-semibold">
                WORKSPACE VIEWS
              </div>

              <div className="space-y-0.5">
                {/* Command Center */}
                <button
                  onClick={() => handleNavClick('COMMAND_CENTER')}
                  className={`w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                    activeView === 'COMMAND_CENTER'
                      ? 'bg-[#161F2D] text-[#F1F5F9] border-l-2 border-[#62CBE8] shadow-xs'
                      : 'text-[#A0AEC0] hover:bg-[#161F2D]/60 hover:text-[#F1F5F9]'
                  }`}
                >
                  <Activity className="w-4 h-4 text-[#62CBE8] shrink-0" />
                  <span>Command Center</span>
                </button>

                {/* Task Board */}
                <button
                  onClick={() => handleNavClick('TASK_BOARD')}
                  className={`w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                    activeView === 'TASK_BOARD'
                      ? 'bg-[#161F2D] text-[#F1F5F9] border-l-2 border-[#62CBE8] shadow-xs'
                      : 'text-[#A0AEC0] hover:bg-[#161F2D]/60 hover:text-[#F1F5F9]'
                  }`}
                >
                  <Kanban className="w-4 h-4 text-[#A0AEC0] shrink-0" />
                  <span>Task Board</span>
                </button>

                {/* Git Activity */}
                <button
                  onClick={() => handleNavClick('GIT_ACTIVITY')}
                  className={`w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                    activeView === 'GIT_ACTIVITY'
                      ? 'bg-[#161F2D] text-[#F1F5F9] border-l-2 border-[#62CBE8] shadow-xs'
                      : 'text-[#A0AEC0] hover:bg-[#161F2D]/60 hover:text-[#F1F5F9]'
                  }`}
                >
                  <GitBranch className="w-4 h-4 text-[#38B982] shrink-0" />
                  <span>Git Activity</span>
                </button>

                {/* AI & Admin Inbox */}
                <button
                  onClick={() => handleNavClick('ADMIN_INBOX')}
                  className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                    activeView === 'ADMIN_INBOX'
                      ? 'bg-[#161F2D] text-[#F1F5F9] border-l-2 border-[#62CBE8] shadow-xs'
                      : 'text-[#A0AEC0] hover:bg-[#161F2D]/60 hover:text-[#F1F5F9]'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <ShieldCheck className={`w-4 h-4 shrink-0 ${isAdmin ? 'text-[#E5B85C]' : 'text-[#77869B]'}`} />
                    <span>Admin Inbox</span>
                  </div>

                  {isAdmin ? (
                    pendingProposalsCount > 0 && (
                      <span className="px-1.5 py-0.2 rounded-full bg-[#E47777] text-[#090D16] text-[10px] font-mono font-bold">
                        {pendingProposalsCount}
                      </span>
                    )
                  ) : (
                    <span title="Admin Role Restricted">
                      <Lock className="w-3.5 h-3.5 text-[#77869B]" />
                    </span>
                  )}
                </button>

                {/* Integrations */}
                <button
                  onClick={() => handleNavClick('INTEGRATIONS')}
                  className={`w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                    activeView === 'INTEGRATIONS'
                      ? 'bg-[#161F2D] text-[#F1F5F9] border-l-2 border-[#62CBE8] shadow-xs'
                      : 'text-[#A0AEC0] hover:bg-[#161F2D]/60 hover:text-[#F1F5F9]'
                  }`}
                >
                  <Zap className="w-4 h-4 text-[#38B982] shrink-0" />
                  <span>Integrations</span>
                </button>

                {/* Audit Ledger */}
                <button
                  onClick={() => handleNavClick('AUDIT_LOG')}
                  className={`w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                    activeView === 'AUDIT_LOG'
                      ? 'bg-[#161F2D] text-[#F1F5F9] border-l-2 border-[#62CBE8] shadow-xs'
                      : 'text-[#A0AEC0] hover:bg-[#161F2D]/60 hover:text-[#F1F5F9]'
                  }`}
                >
                  <Clock className="w-4 h-4 text-[#62CBE8] shrink-0" />
                  <span>Audit Ledger</span>
                </button>

                {/* Settings */}
                <button
                  onClick={() => handleNavClick('SETTINGS')}
                  className={`w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                    activeView === 'SETTINGS'
                      ? 'bg-[#161F2D] text-[#F1F5F9] border-l-2 border-[#62CBE8] shadow-xs'
                      : 'text-[#A0AEC0] hover:bg-[#161F2D]/60 hover:text-[#F1F5F9]'
                  }`}
                >
                  <Settings className="w-4 h-4 text-[#A0AEC0] shrink-0" />
                  <span>Settings</span>
                </button>
              </div>
            </div>

            {/* Team Communication Channels */}
            <div>
              <div className="px-2 mb-1.5 text-[11px] font-sans uppercase tracking-wider text-[#77869B] font-semibold">
                CHANNELS
              </div>

              <div className="space-y-0.5">
                {CHANNELS.map((channel) => (
                  <button
                    key={channel.id}
                    onClick={() => handleChannelClick(channel.id)}
                    className={`w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                      activeView === 'CHAT' && activeChannel === channel.id
                        ? 'bg-[#161F2D] text-[#F1F5F9] border-l-2 border-[#62CBE8]'
                        : 'text-[#A0AEC0] hover:bg-[#161F2D]/60 hover:text-[#F1F5F9]'
                    }`}
                  >
                    <Hash className="w-3.5 h-3.5 text-[#77869B] shrink-0" />
                    <span>{channel.name}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* User Profile Bar */}
          <div className="h-14 bg-[#090D16] px-3 flex items-center justify-between border-t border-[#263246]">
            <div className="flex items-center gap-2 min-w-0">
              <div className="relative shrink-0">
                <img
                  src={currentUser.avatar}
                  alt={currentUser.name}
                  className="w-7 h-7 rounded-full object-cover border border-[#263246]"
                />
                <span className="absolute bottom-0 right-0 w-2 h-2 bg-[#38B982] rounded-full border border-[#090D16]" />
              </div>

              <div className="min-w-0">
                <div className="text-xs font-semibold text-[#F1F5F9] truncate font-sans leading-tight">
                  {currentUser.name}
                </div>
                <div className="text-[11px] font-sans text-[#A0AEC0] flex items-center gap-1">
                  <span className={isAdmin ? 'text-[#62CBE8] font-medium' : 'text-[#38B982] font-medium'}>
                    {isAdmin ? 'Project Lead' : 'Developer'}
                  </span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-1">
              <button
                onClick={onToggleRole}
                className="px-2 py-0.5 hover:bg-[#161F2D] text-[#A0AEC0] hover:text-[#F1F5F9] rounded text-[10px] font-sans border border-[#263246] transition-colors"
                title="Toggle role between ADMIN and DEVELOPER"
              >
                Toggle
              </button>
              <button
                onClick={onLogout}
                className="p-1.5 hover:bg-[#161F2D] text-[#A0AEC0] hover:text-[#E47777] rounded transition-colors"
                title="Sign Out"
              >
                <LogOut className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 3. MAIN STAGE */}
      <div className="flex-1 flex flex-col min-w-0 bg-[#090D16] overflow-hidden relative">
        {/* Atmospheric particle backdrop */}
        <div className="absolute inset-0 pointer-events-none z-0">
          <ParticleBackground intensity="restrained" className="opacity-15" />
        </div>

        {/* Stage Content */}
        <div className="flex-1 min-w-0 overflow-hidden relative z-10">
          {children}
        </div>
      </div>

      {/* 4. RIGHT CONTEXT PANEL TOGGLE & PANEL */}
      {/* Desktop expand button when collapsed */}
      {!isRightSidebarOpen && (
        <button
          onClick={() => setIsRightSidebarOpen(true)}
          className="hidden xl:flex fixed right-3 top-3 z-30 p-2 rounded-lg bg-[#111925] border border-[#263246] text-[#A0AEC0] hover:text-[#62CBE8] hover:border-[#62CBE8]/40 shadow-lg transition-colors items-center gap-1.5 text-xs font-sans font-medium"
          title="Open Active Context Panel"
        >
          <PanelRight className="w-4 h-4 text-[#62CBE8]" />
          <span>Context</span>
        </button>
      )}

      {/* Active Context Panel (collapsible) */}
      {isRightSidebarOpen && (
        <div className="hidden xl:flex w-56 bg-[#111925] border-l border-[#263246] flex-col shrink-0">
          <div className="h-14 px-3.5 border-b border-[#263246] flex items-center justify-between">
            <span className="text-[11px] font-sans font-semibold uppercase tracking-wider text-[#A0AEC0] flex items-center gap-2">
              <Users className="w-3.5 h-3.5 text-[#62CBE8]" />
              <span>Active Context</span>
            </span>
            <button
              onClick={() => setIsRightSidebarOpen(false)}
              className="p-1 rounded hover:bg-[#161F2D] text-[#77869B] hover:text-[#F1F5F9] transition-colors"
              title="Collapse Active Context"
            >
              <PanelRightClose className="w-4 h-4" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-6">
            {/* Active Blockers Ticker */}
            <div>
              <div className="text-[11px] font-semibold font-sans uppercase tracking-wider text-[#E47777] flex items-center gap-1.5 mb-2.5">
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>Active Blockers ({blockedTasks.length})</span>
              </div>

              {blockedTasks.length === 0 ? (
                <div className="text-xs text-[#A0AEC0] font-sans bg-[#090D16] p-3 rounded-lg border border-[#263246]">
                  Zero confirmed blockers.
                </div>
              ) : (
                <div className="space-y-2">
                  {blockedTasks.map((bt) => (
                    <div
                      key={bt.id}
                      onClick={() => handleNavClick('TASK_BOARD')}
                      className="p-2.5 bg-[#090D16] border border-[#E47777]/30 hover:border-[#E47777] rounded-lg text-xs cursor-pointer transition-colors"
                    >
                      <div className="font-mono text-[#E47777] font-semibold text-[11px]">{bt.id}</div>
                      <div className="text-[#F1F5F9] font-medium text-[11px] truncate mt-0.5 font-sans">{bt.title}</div>
                      {bt.waitingOn && (
                        <div className="text-[11px] text-[#A0AEC0] mt-1 font-sans truncate">
                          Wait: <span className="text-[#E47777] font-medium">{bt.waitingOn}</span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Team Presence */}
            <div>
              <div className="text-[11px] font-semibold font-sans uppercase tracking-wider text-[#A0AEC0] mb-2.5 flex items-center justify-between">
                <span>TEAM PRESENCE</span>
                <span className="text-[10px] font-sans font-medium px-1.5 py-0.5 rounded bg-[#090D16] text-[#38B982] border border-[#38B982]/30">
                  {(teamMembers || [currentUser]).length} Active
                </span>
              </div>

              <div className="space-y-2">
                {(teamMembers && teamMembers.length > 0 ? teamMembers : [currentUser]).map((member) => (
                  <div key={member.id} className="flex items-center gap-2.5 py-1 px-1 rounded hover:bg-[#161F2D]/50 transition-colors">
                    <span className="w-2 h-2 rounded-full bg-[#38B982] shrink-0" />
                    <div className="min-w-0">
                      <div className="text-xs font-semibold text-[#F1F5F9] truncate font-sans">{member.name}</div>
                      <div className="text-[11px] text-[#A0AEC0] font-sans">
                        {member.role === 'ADMIN' ? 'Lead' : 'Developer'} · <span className="text-[#77869B]">{member.id === currentUser.id ? 'You' : 'Active'}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default WorkspaceShell
