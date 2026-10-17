import React, { useState } from 'react'
import { 
  Settings, 
  Sliders, 
  User as UserIcon, 
  ShieldAlert, 
  Save, 
  Key, 
  Bell, 
  Check, 
  RefreshCw,
  Copy 
} from 'lucide-react'
import type { User } from '../../types/auth'
import type { ProjectStats } from '../../types/models'

interface SettingsViewProps {
  currentUser: User
  stats: ProjectStats
  onUpdateStats: (newStats: Partial<ProjectStats>) => void
  onToggleRole: () => void
  onRequestResetDemo: () => void
  onShowToast: (title: string, description?: string) => void
  onGenerateToken?: () => string
  apiAccessToken?: string
}

export const SettingsView: React.FC<SettingsViewProps> = ({
  currentUser,
  stats,
  onUpdateStats,
  onToggleRole,
  onRequestResetDemo,
  onShowToast,
  onGenerateToken,
  apiAccessToken,
}) => {
  const [tokenCopied, setTokenCopied] = useState(false)
  const [activeTab, setActiveTab] = useState<'WORKSPACE' | 'ACCOUNT'>('WORKSPACE')
  const [workspaceName, setWorkspaceName] = useState(stats.repoName)
  const [activeSprint, setActiveSprint] = useState(stats.activeSprint)
  const [aiSensitivity, setAiSensitivity] = useState(85)
  const [notificationsEnabled, setNotificationsEnabled] = useState(true)

  const handleSaveWorkspace = (e: React.FormEvent) => {
    e.preventDefault()
    onUpdateStats({
      repoName: workspaceName,
      activeSprint,
    })
    onShowToast('Workspace Settings Saved', 'Project metadata and sprint targets updated.')
  }

  return (
    <div className="h-full overflow-y-auto p-4 sm:p-6 bg-[#090D16]">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#263246]">
          <div>
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-[#111925] border border-[#263246] flex items-center justify-center text-[#62CBE8]">
                <Settings className="w-4 h-4" />
              </div>
              <h1 className="text-lg sm:text-xl font-normal text-[#F1F5F9] tracking-wide font-display">Project &amp; Account Settings</h1>
            </div>
            <p className="text-xs text-[#77869B] mt-1 font-sans">
              Sprint Configuration · Access Control · Detection Thresholds
            </p>
          </div>

          {/* Tab Selector */}
          <div className="flex items-center gap-1 bg-[#111925] p-1 rounded-lg border border-[#263246] text-xs font-sans self-start sm:self-auto">
            <button
              onClick={() => setActiveTab('WORKSPACE')}
              className={`px-3 py-1 rounded-md font-semibold transition-all ${
                activeTab === 'WORKSPACE'
                  ? 'bg-[#62CBE8] text-[#07131C]'
                  : 'text-[#A0AEC0] hover:text-[#F1F5F9]'
              }`}
            >
              Workspace
            </button>
            <button
              onClick={() => setActiveTab('ACCOUNT')}
              className={`px-3 py-1 rounded-md font-semibold transition-all ${
                activeTab === 'ACCOUNT'
                  ? 'bg-[#62CBE8] text-[#07131C]'
                  : 'text-[#A0AEC0] hover:text-[#F1F5F9]'
              }`}
            >
              Account
            </button>
          </div>
        </div>

        {/* WORKSPACE TAB */}
        {activeTab === 'WORKSPACE' && (
          <div className="space-y-5">
            <form onSubmit={handleSaveWorkspace} className="bg-[#111925] border border-[#263246] rounded-xl p-5 shadow-xs space-y-4">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-[#F1F5F9] flex items-center gap-2 font-sans">
                <Sliders className="w-4 h-4 text-[#62CBE8]" />
                <span>General Sprint Parameters</span>
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-sans">
                <div>
                  <label className="block text-[11px] font-semibold text-[#A0AEC0] uppercase tracking-wider mb-1.5 font-sans">
                    Workspace Identifier
                  </label>
                  <input
                    type="text"
                    value={workspaceName}
                    onChange={(e) => setWorkspaceName(e.target.value)}
                    className="w-full bg-[#161F2D] border border-[#263246] focus:border-[#62CBE8] rounded-lg px-3 py-2 text-xs sm:text-sm text-[#F1F5F9] outline-none font-mono transition-colors"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-[#A0AEC0] uppercase tracking-wider mb-1.5 font-sans">
                    Active Sprint Designation
                  </label>
                  <input
                    type="text"
                    value={activeSprint}
                    onChange={(e) => setActiveSprint(e.target.value)}
                    className="w-full bg-[#161F2D] border border-[#263246] focus:border-[#62CBE8] rounded-lg px-3 py-2 text-xs sm:text-sm text-[#F1F5F9] outline-none font-sans transition-colors"
                  />
                </div>
              </div>

              {/* Sensitivity slider */}
              <div className="pt-2">
                <div className="flex items-center justify-between text-xs font-mono mb-2">
                  <span className="text-[#A0AEC0]">AI Blocker Detection Confidence:</span>
                  <strong className="text-[#62CBE8]">{aiSensitivity}% Minimum</strong>
                </div>
                <input
                  type="range"
                  min="60"
                  max="95"
                  value={aiSensitivity}
                  onChange={(e) => setAiSensitivity(Number(e.target.value))}
                  className="w-full accent-[#62CBE8] bg-[#161F2D] rounded-lg cursor-pointer h-1.5"
                />
                <span className="text-[11px] text-[#77869B] font-sans mt-1 block">
                  Higher threshold prevents false positives; lower captures tentative language.
                </span>
              </div>

              <div className="flex items-center justify-end pt-3 border-t border-[#263246]">
                <button
                  type="submit"
                  className="px-4 py-2 bg-[#62CBE8] hover:bg-[#52c1df] text-[#090D16] font-semibold text-xs rounded-lg flex items-center gap-2 transition-colors font-mono"
                >
                  <Save className="w-3.5 h-3.5" />
                  <span>Save Parameters</span>
                </button>
              </div>
            </form>

            {/* Reset / Destructive Zone */}
            <div className="bg-[#111925] border border-[#E47777]/30 rounded-xl p-5 shadow-xs space-y-3">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-[#E47777] flex items-center gap-2 font-mono">
                <ShieldAlert className="w-4 h-4" />
                <span>Clear Workspace Data</span>
              </h3>
              <p className="text-xs text-[#A0AEC0] leading-relaxed font-sans">
                Purge all tasks, chat messages, and blocker proposals created in this session, returning the workspace to a clean, empty state.
              </p>
              <button
                type="button"
                onClick={onRequestResetDemo}
                className="px-3.5 py-1.5 bg-[#161F2D] hover:bg-[#E47777]/20 text-[#E47777] border border-[#E47777]/40 text-xs font-mono font-medium rounded-lg flex items-center gap-2 transition-colors"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Clear All Workspace Data</span>
              </button>
            </div>
          </div>
        )}

        {/* ACCOUNT TAB */}
        {activeTab === 'ACCOUNT' && (
          <div className="bg-[#111925] border border-[#263246] rounded-xl p-5 shadow-xs space-y-5">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-[#F1F5F9] flex items-center gap-2 font-mono">
              <UserIcon className="w-4 h-4 text-[#62CBE8]" />
              <span>Current User Profile &amp; Role</span>
            </h3>

            <div className="flex items-center gap-3.5 p-3.5 bg-[#161F2D] rounded-lg border border-[#263246]">
              <img
                src={currentUser.avatar}
                alt={currentUser.name}
                className="w-12 h-12 rounded-full object-cover border border-[#263246]"
              />
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <h4 className="text-sm font-semibold text-[#F1F5F9] font-sans">{currentUser.name}</h4>
                  <span className={`text-[10px] font-sans font-semibold px-2 py-0.5 rounded border ${
                    currentUser.role === 'ADMIN'
                      ? 'bg-[#62CBE8]/15 text-[#62CBE8] border-[#62CBE8]/30'
                      : 'bg-[#38B982]/15 text-[#38B982] border-[#38B982]/30'
                  }`}>
                    {currentUser.role === 'ADMIN' ? 'Project Lead' : 'Developer'}
                  </span>
                </div>
                <div className="text-xs text-[#77869B] font-mono">@{currentUser.handle} · {currentUser.email}</div>
                <div className="text-xs text-[#A0AEC0]">{currentUser.title}</div>
              </div>
            </div>

            {/* Quick Role Toggle */}
            <div className="p-3.5 bg-[#161F2D] rounded-lg border border-[#263246] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <span className="text-xs font-medium text-[#F1F5F9] block">RBAC Role Switcher</span>
                <span className="text-[11px] text-[#77869B]">
                  Currently acting as {currentUser.role}. Toggle between Lead (Admin) and Engineer (Developer).
                </span>
              </div>
              <button
                type="button"
                onClick={() => {
                  onToggleRole()
                  onShowToast('Role Toggled', `Active view permissions updated for ${currentUser.role === 'ADMIN' ? 'Developer' : 'Admin'}.`)
                }}
                className="px-3.5 py-1.5 bg-[#62CBE8] hover:bg-[#79D6EE] text-[#07131C] font-semibold text-xs rounded-lg font-sans shrink-0 transition-colors self-start sm:self-auto"
              >
                Switch to {currentUser.role === 'ADMIN' ? 'Developer' : 'Admin'}
              </button>
            </div>

            {/* Notification Rules */}
            <div className="p-3.5 bg-[#161F2D] rounded-lg border border-[#263246] flex items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <Bell className="w-4 h-4 text-[#62CBE8]" />
                <div>
                  <span className="text-xs font-medium text-[#F1F5F9] block">Real-time Blocker Alert Notifications</span>
                  <span className="text-[11px] text-[#77869B]">
                    Show toast banner when a dependency blocker is extracted in team chat.
                  </span>
                </div>
              </div>
              <button
                type="button"
                onClick={() => {
                  setNotificationsEnabled(!notificationsEnabled)
                  onShowToast('Notification Preference Updated')
                }}
                className={`w-10 h-5.5 rounded-full transition-colors relative flex items-center px-0.5 ${
                  notificationsEnabled ? 'bg-[#38B982]' : 'bg-[#263246]'
                }`}
              >
                <div className={`w-4 h-4 bg-white rounded-full transition-transform ${
                  notificationsEnabled ? 'translate-x-4.5' : 'translate-x-0'
                }`} />
              </button>
            </div>

            {/* API Access Token */}
            <div className="p-3.5 bg-[#161F2D] rounded-lg border border-[#263246] space-y-2 text-xs font-mono">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-[#F1F5F9] font-medium">
                  <Key className="w-3.5 h-3.5 text-[#E5B85C]" />
                  <span>Workspace Access Token</span>
                </div>
                {onGenerateToken && (
                  <button
                    type="button"
                    onClick={() => onGenerateToken()}
                    className="text-[10px] text-[#62CBE8] hover:underline"
                  >
                    {apiAccessToken ? 'Regenerate Token' : 'Generate Secret Token'}
                  </button>
                )}
              </div>
              {apiAccessToken ? (
                <div className="p-2 bg-[#090D16] border border-[#263246] rounded-md text-[#77869B] flex items-center justify-between">
                  <span className="text-[#F1F5F9] font-mono truncate max-w-[280px]">{apiAccessToken}</span>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => {
                        navigator.clipboard.writeText(apiAccessToken)
                        setTokenCopied(true)
                        setTimeout(() => setTokenCopied(false), 2000)
                      }}
                      className="text-[#62CBE8] hover:text-white"
                      title="Copy token"
                    >
                      {tokenCopied ? <Check className="w-3.5 h-3.5 text-[#38B982]" /> : <Copy className="w-3.5 h-3.5" />}
                    </button>
                    <span className="text-[#38B982] font-semibold text-[10px] flex items-center gap-1">
                      <Check className="w-3 h-3" />
                      ACTIVE
                    </span>
                  </div>
                </div>
              ) : (
                <div className="p-2 bg-[#090D16] border border-[#263246] rounded-md text-[#77869B] flex items-center justify-between">
                  <span>No workspace secret token generated</span>
                  {onGenerateToken && (
                    <button
                      type="button"
                      onClick={() => onGenerateToken()}
                      className="px-2 py-0.5 bg-[#62CBE8] text-[#07131C] font-semibold text-[10px] rounded hover:bg-[#79D6EE]"
                    >
                      Generate Token
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default SettingsView
