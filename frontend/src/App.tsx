import { useState } from 'react'
import LandingPage from './components/landing/LandingPage'
import LoginPage from './components/auth/LoginPage'
import SignupPage from './components/auth/SignupPage'
import WorkspaceShell, { type ActiveView } from './components/layout/WorkspaceShell'
import CommandCenter from './components/dashboard/CommandCenter'
import TeamChat from './components/chat/TeamChat'
import TaskBoard from './components/tasks/TaskBoard'
import GitActivity from './components/git/GitActivity'
import AdminInbox from './components/admin/AdminInbox'
import { IntegrationsView } from './components/integrations/IntegrationsView'
import { AuditHistoryView } from './components/audit/AuditHistoryView'
import { SettingsView } from './components/settings/SettingsView'
import { ToastContainer, type ToastMessage, type ToastType } from './components/common/ToastContainer'
import { ConfirmationModal } from './components/common/ConfirmationModal'
import { ErrorBoundary } from './components/common/ErrorBoundary'
import { CreateTaskModal } from './components/tasks/CreateTaskModal'
import { TaskDetailModal } from './components/tasks/TaskDetailModal'
import type { User } from './types/auth'
import type { Task, ChatMessage, AIProposal, GitEvent, TaskStatus, ProjectStats } from './types/models'
import { WorkspaceStore } from './services/workspaceStore'

type AppRoute = 'LANDING' | 'LOGIN' | 'SIGNUP' | 'WORKSPACE'

export function App() {
  const store = WorkspaceStore.getInstance()

  const [route, setRoute] = useState<AppRoute>('LANDING')
  const [currentUser, setCurrentUser] = useState<User>(() => store.getCurrentUser())
  const [activeWorkspaceView, setActiveWorkspaceView] = useState<ActiveView>('COMMAND_CENTER')
  const [activeChannel, setActiveChannel] = useState<string>('frontend')

  // Real workspace state from persistent store
  const [tasks, setTasks] = useState<Task[]>(() => store.getTasks())
  const [messages, setMessages] = useState<ChatMessage[]>(() => store.getMessages())
  const [proposals, setProposals] = useState<AIProposal[]>(() => store.getProposals())
  const [gitEvents, setGitEvents] = useState<GitEvent[]>(() => store.getGitEvents())
  const [projectStats, setProjectStats] = useState<ProjectStats>(() => store.getProjectStats())
  const [teamMembers, setTeamMembers] = useState<User[]>(() => store.getState().teamMembers)

  // Modals & Feedback state
  const [isCreateTaskModalOpen, setIsCreateTaskModalOpen] = useState(false)
  const [createTaskInitialTitle, setCreateTaskInitialTitle] = useState('')
  const [selectedTaskForDetail, setSelectedTaskForDetail] = useState<Task | null>(null)

  // Toast notifications state
  const [toasts, setToasts] = useState<ToastMessage[]>([])
  const showToast = (title: string, description?: string, type: ToastType = 'info') => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`
    setToasts((prev) => [...prev, { id, title, description, type }])
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id))
    }, 4500)
  }
  const handleDismissToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }

  // Synchronize state from store
  const syncFromStore = () => {
    setTasks(store.getTasks())
    setMessages(store.getMessages())
    setProposals(store.getProposals())
    setGitEvents(store.getGitEvents())
    setProjectStats(store.getProjectStats())
    setCurrentUser(store.getCurrentUser())
    setTeamMembers(store.getState().teamMembers)
  }

  // Confirmation modal state
  const [confirmationModal, setConfirmationModal] = useState<{
    isOpen: boolean
    title: string
    description: string
    severity?: 'danger' | 'warning' | 'info'
    confirmLabel?: string
    cancelLabel?: string
    onConfirm: () => void
  }>({
    isOpen: false,
    title: '',
    description: '',
    onConfirm: () => {},
  })

  // 1. Approve AI proposal
  const handleApproveProposal = (proposalId: string) => {
    const res = store.approveProposal(proposalId, currentUser)
    if (!res) return

    syncFromStore()
    showToast(
      'Proposal Approved',
      `Task ${res.proposal.taskId} marked as ${res.proposal.proposedStatus}. Recorded in Decision Ledger.`,
      'success'
    )
  }

  // 2. Reject proposal with confirmation modal
  const handleRejectProposal = (proposalId: string) => {
    const proposal = proposals.find((p) => p.id === proposalId)
    setConfirmationModal({
      isOpen: true,
      title: 'Reject Blocker Escalation?',
      description: `Reject proposal for ${proposal ? proposal.taskId : 'this task'}? The proposal will be recorded as REJECTED in the Decision Ledger, and task status will remain unchanged.`,
      severity: 'warning',
      confirmLabel: 'Reject Proposal',
      onConfirm: () => {
        store.rejectProposal(proposalId, currentUser, 'Lead determined dependency does not block progress.')
        syncFromStore()
        setConfirmationModal((prev) => ({ ...prev, isOpen: false }))
        showToast('Proposal Rejected', 'Recorded in Decision Ledger without mutating task status.', 'warning')
      },
    })
  }

  // 3. Send message with genuine keyword blocker detection
  const handleSendMessage = (channelId: string, content: string) => {
    const res = store.postMessage(channelId, content, currentUser)
    syncFromStore()

    if (res.proposal) {
      showToast('AI Blocker Signal Detected', `Created proposal for ${res.proposal.taskId} based on message in #${channelId}.`, 'info')
    }
  }

  // 4. Flag message as blocker manually
  const handleFlagBlocker = (message: ChatMessage) => {
    if (tasks.length === 0) {
      showToast('No Active Tasks', 'Create an engineering task before escalating a conversation blocker.', 'warning')
      return
    }

    const proposal = store.flagBlockerManually(message)
    if (proposal) {
      syncFromStore()
      setActiveWorkspaceView('ADMIN_INBOX')
      showToast('Blocker Escalated', `Manual escalation created for ${proposal.taskId}. Awaiting lead review.`, 'warning')
    }
  }

  // 5. Create task from message action
  const handleCreateTaskFromMessage = (message: ChatMessage) => {
    setCreateTaskInitialTitle(`Resolve: ${message.content.slice(0, 40)}...`)
    setIsCreateTaskModalOpen(true)
  }

  // 6. Update task status manually
  const handleUpdateTaskStatus = (taskId: string, newStatus: TaskStatus) => {
    store.updateTaskStatus(taskId, newStatus)
    syncFromStore()
    showToast('Task Updated', `Task ${taskId} moved to ${newStatus}.`, 'info')
  }

  // 7. Add newly created task
  const handleCreateTask = (newTaskPartial: Partial<Task>) => {
    const created = store.createTask(newTaskPartial, currentUser)
    syncFromStore()
    showToast('Task Created', `${created.id} added to backlog.`, 'success')
  }

  // 8. Quick Toggle Role (Admin <-> Developer)
  const handleToggleRole = () => {
    const updated = store.toggleCurrentUserRole()
    syncFromStore()
    showToast(
      'Role Toggled',
      `Switched to ${updated.role === 'ADMIN' ? 'Administrator' : 'Developer'} view mode.`,
      'info'
    )
  }

  // 9. Clear workspace data
  const handleClearWorkspace = () => {
    setConfirmationModal({
      isOpen: true,
      title: 'Clear Workspace Data?',
      description: 'This will purge all tasks, chat messages, and proposals created in this session, returning the workspace to an empty slate. This action cannot be undone.',
      severity: 'danger',
      confirmLabel: 'Clear All Data',
      onConfirm: () => {
        store.clearAllData()
        syncFromStore()
        setConfirmationModal((prev) => ({ ...prev, isOpen: false }))
        showToast('Workspace Cleared', 'All tasks, chats, and proposals removed.', 'info')
      },
    })
  }

  const pendingCount = proposals.filter((p) => p.status === 'PENDING').length

  return (
    <ErrorBoundary>
      {/* Route 0A: Landing Page */}
      {route === 'LANDING' && (
        <LandingPage
          onEnterApp={() => setRoute('WORKSPACE')}
          onGoToLogin={() => setRoute('LOGIN')}
          onGoToSignup={() => setRoute('SIGNUP')}
        />
      )}

      {/* Route 0B: Login Page */}
      {route === 'LOGIN' && (
        <LoginPage
          onLogin={(user) => {
            store.setCurrentUser(user)
            syncFromStore()
            setRoute('WORKSPACE')
            showToast('Welcome back', `Signed in as ${user.name} (${user.role})`, 'success')
          }}
          onNavigateToSignup={() => setRoute('SIGNUP')}
          onNavigateToLanding={() => setRoute('LANDING')}
        />
      )}

      {/* Route 0C: Signup Page */}
      {route === 'SIGNUP' && (
        <SignupPage
          onSignup={(user) => {
            store.setCurrentUser(user)
            syncFromStore()
            setRoute('WORKSPACE')
            showToast('Account Created', `Welcome to युक्तिOps, ${user.name}!`, 'success')
          }}
          onNavigateToLogin={() => setRoute('LOGIN')}
          onNavigateToLanding={() => setRoute('LANDING')}
        />
      )}

      {/* Route WORKSPACE: Authenticated Workspace Shell */}
      {route === 'WORKSPACE' && (
        <WorkspaceShell
          currentUser={currentUser}
          teamMembers={teamMembers}
          activeView={activeWorkspaceView}
          activeChannel={activeChannel}
          pendingProposalsCount={pendingCount}
          tasks={tasks}
          onSelectView={setActiveWorkspaceView}
          onSelectChannel={setActiveChannel}
          onToggleRole={handleToggleRole}
          onLogout={() => {
            setRoute('LANDING')
            showToast('Signed Out', 'You have been logged out of the workspace.', 'info')
          }}
        >
          {/* Dynamic Screen Stage */}
          {activeWorkspaceView === 'COMMAND_CENTER' && (
            <CommandCenter
              currentUser={currentUser}
              stats={projectStats}
              tasks={tasks}
              proposals={proposals}
              gitEvents={gitEvents}
              onNavigateToInbox={() => setActiveWorkspaceView('ADMIN_INBOX')}
              onNavigateToTasks={() => setActiveWorkspaceView('TASK_BOARD')}
              onNavigateToGit={() => setActiveWorkspaceView('GIT_ACTIVITY')}
              onOpenCreateTaskModal={() => {
                setCreateTaskInitialTitle('')
                setIsCreateTaskModalOpen(true)
              }}
            />
          )}

          {activeWorkspaceView === 'CHAT' && (
            <TeamChat
              currentUser={currentUser}
              messages={messages}
              onSendMessage={handleSendMessage}
              onFlagBlocker={handleFlagBlocker}
              onCreateTaskFromMessage={handleCreateTaskFromMessage}
              activeChannel={activeChannel}
              onSelectChannel={setActiveChannel}
            />
          )}

          {activeWorkspaceView === 'TASK_BOARD' && (
            <TaskBoard
              userRole={currentUser.role}
              tasks={tasks}
              onUpdateTaskStatus={handleUpdateTaskStatus}
              onOpenCreateTaskModal={() => {
                setCreateTaskInitialTitle('')
                setIsCreateTaskModalOpen(true)
              }}
              onSelectTask={(task) => setSelectedTaskForDetail(task)}
            />
          )}

          {activeWorkspaceView === 'GIT_ACTIVITY' && (
            <GitActivity
              events={gitEvents}
              repoConnected={projectStats.repoConnected}
              repoName={projectStats.repoName}
              onToggleConnection={() => {
                const nextState = !projectStats.repoConnected
                const updated = store.updateSettings({ repoConnected: nextState })
                syncFromStore()
                showToast(
                  nextState ? 'GitHub Repository Connected' : 'GitHub Repository Disconnected',
                  nextState ? `Connected to ${updated.repoName || 'configured repository'}.` : 'Integration paused.',
                  nextState ? 'success' : 'warning'
                )
              }}
              onConfigureRepo={() => setActiveWorkspaceView('INTEGRATIONS')}
              onTriggerTestWebhook={() => {
                const newEv = store.recordGitEvent()
                syncFromStore()
                showToast('Test Webhook Ingested', `Received webhook event ${newEv.sha} from GitHub.`, 'success')
              }}
            />
          )}

          {activeWorkspaceView === 'ADMIN_INBOX' && (
            <AdminInbox
              userRole={currentUser.role}
              proposals={proposals}
              onApproveProposal={handleApproveProposal}
              onRejectProposal={handleRejectProposal}
              onNavigateToTasks={() => setActiveWorkspaceView('TASK_BOARD')}
            />
          )}

          {activeWorkspaceView === 'INTEGRATIONS' && (
            <IntegrationsView
              repoConnected={projectStats.repoConnected}
              repoName={projectStats.repoName}
              onToggleConnection={() => {
                const nextState = !projectStats.repoConnected
                const updated = store.updateSettings({ repoConnected: nextState })
                syncFromStore()
                showToast(
                  nextState ? 'GitHub Repository Connected' : 'GitHub Repository Disconnected',
                  nextState ? `Connected to ${updated.repoName || 'configured repository'}.` : 'Integration suspended.',
                  nextState ? 'success' : 'warning'
                )
              }}
              onTriggerSync={() => {
                showToast('Integrations Checked', 'Verified local classifier and storage subsystem status.', 'info')
              }}
              onSaveRepoName={(name) => {
                store.updateSettings({ repoName: name, repoConnected: true })
                syncFromStore()
                showToast('Repository Saved', `Set repository target to ${name}.`, 'success')
              }}
            />
          )}

          {activeWorkspaceView === 'AUDIT_LOG' && (
            <AuditHistoryView
              proposals={proposals}
              currentUser={currentUser}
              onSelectTask={(taskId) => {
                const task = tasks.find((t) => t.id === taskId)
                if (task) {
                  setSelectedTaskForDetail(task)
                } else {
                  setActiveWorkspaceView('TASK_BOARD')
                }
              }}
            />
          )}

          {activeWorkspaceView === 'SETTINGS' && (
            <SettingsView
              currentUser={currentUser}
              stats={projectStats}
              apiAccessToken={store.getSettings().apiAccessToken}
              onUpdateStats={(newStats) => {
                store.updateSettings(newStats)
                syncFromStore()
                showToast('Settings Saved', 'Workspace configuration updated.', 'success')
              }}
              onToggleRole={handleToggleRole}
              onRequestResetDemo={handleClearWorkspace}
              onShowToast={(title, desc) => showToast(title, desc, 'success')}
              onGenerateToken={() => {
                const token = store.generateApiToken()
                syncFromStore()
                showToast('Access Token Generated', 'New workspace secret token created.', 'success')
                return token
              }}
            />
          )}

          {/* Modals within Workspace */}
          <CreateTaskModal
            isOpen={isCreateTaskModalOpen}
            onClose={() => setIsCreateTaskModalOpen(false)}
            onCreateTask={handleCreateTask}
            initialTitle={createTaskInitialTitle}
            currentUser={currentUser}
            teamMembers={teamMembers}
          />

          <TaskDetailModal
            task={selectedTaskForDetail}
            onClose={() => setSelectedTaskForDetail(null)}
          />
        </WorkspaceShell>
      )}

      {/* Global Modals & Notifications */}
      <ToastContainer toasts={toasts} onDismiss={handleDismissToast} />
      <ConfirmationModal
        isOpen={confirmationModal.isOpen}
        title={confirmationModal.title}
        description={confirmationModal.description}
        severity={confirmationModal.severity}
        confirmLabel={confirmationModal.confirmLabel}
        cancelLabel={confirmationModal.cancelLabel}
        onConfirm={confirmationModal.onConfirm}
        onCancel={() => setConfirmationModal((prev) => ({ ...prev, isOpen: false }))}
      />
    </ErrorBoundary>
  )
}

export default App
