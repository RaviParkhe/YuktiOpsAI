import type { Task, ChatMessage, AIProposal, GitEvent, ProjectStats, TaskStatus } from '../types/models'
import type { User, UserRole } from '../types/auth'

const STORAGE_KEY = 'yuktiops_workspace_data_v2'

export interface WorkspaceSettings {
  workspaceName: string
  activeSprint: string
  repoConnected: boolean
  repoName: string
  aiSensitivity: number
  notificationsEnabled: boolean
  apiAccessToken: string
}

export interface WorkspaceState {
  currentUser: User
  tasks: Task[]
  messages: ChatMessage[]
  proposals: AIProposal[]
  gitEvents: GitEvent[]
  settings: WorkspaceSettings
  teamMembers: User[]
}

const DEFAULT_ADMIN_USER: User = {
  id: 'usr-admin-primary',
  name: 'Lead Engineer',
  handle: 'lead_eng',
  email: 'lead@yuktiops.dev',
  role: 'ADMIN',
  title: 'Project Lead',
  avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=120&auto=format&fit=crop&q=80',
  isOnline: true,
}

const DEFAULT_SETTINGS: WorkspaceSettings = {
  workspaceName: 'YuktiOps Core',
  activeSprint: '',
  repoConnected: false,
  repoName: '',
  aiSensitivity: 85,
  notificationsEnabled: true,
  apiAccessToken: '',
}

export class WorkspaceStore {
  private static instance: WorkspaceStore
  private state: WorkspaceState

  private constructor() {
    this.state = this.loadFromStorage()
  }

  public static getInstance(): WorkspaceStore {
    if (!WorkspaceStore.instance) {
      WorkspaceStore.instance = new WorkspaceStore()
    }
    return WorkspaceStore.instance
  }

  private loadFromStorage(): WorkspaceState {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (raw) {
        const parsed = JSON.parse(raw)
        return {
          currentUser: parsed.currentUser || DEFAULT_ADMIN_USER,
          tasks: Array.isArray(parsed.tasks) ? parsed.tasks : [],
          messages: Array.isArray(parsed.messages) ? parsed.messages : [],
          proposals: Array.isArray(parsed.proposals) ? parsed.proposals : [],
          gitEvents: Array.isArray(parsed.gitEvents) ? parsed.gitEvents : [],
          settings: { ...DEFAULT_SETTINGS, ...(parsed.settings || {}) },
          teamMembers: Array.isArray(parsed.teamMembers) && parsed.teamMembers.length > 0 
            ? parsed.teamMembers 
            : [parsed.currentUser || DEFAULT_ADMIN_USER],
        }
      }
    } catch (e) {
      console.warn('Could not load workspace storage:', e)
    }

    return {
      currentUser: DEFAULT_ADMIN_USER,
      tasks: [],
      messages: [],
      proposals: [],
      gitEvents: [],
      settings: DEFAULT_SETTINGS,
      teamMembers: [DEFAULT_ADMIN_USER],
    }
  }

  private saveToStorage(): void {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.state))
    } catch (e) {
      console.error('Failed to save workspace state:', e)
    }
  }

  public getState(): WorkspaceState {
    return { ...this.state }
  }

  public getCurrentUser(): User {
    return this.state.currentUser
  }

  public setCurrentUser(user: User): void {
    this.state.currentUser = user
    if (!this.state.teamMembers.some((m) => m.id === user.id)) {
      this.state.teamMembers = [user, ...this.state.teamMembers]
    }
    this.saveToStorage()
  }

  public toggleCurrentUserRole(): User {
    const nextRole: UserRole = this.state.currentUser.role === 'ADMIN' ? 'DEVELOPER' : 'ADMIN'
    this.state.currentUser = {
      ...this.state.currentUser,
      role: nextRole,
      title: nextRole === 'ADMIN' ? 'Project Lead' : 'Software Engineer',
    }
    this.saveToStorage()
    return this.state.currentUser
  }

  public getTasks(): Task[] {
    return [...this.state.tasks]
  }

  public createTask(taskData: Partial<Task>, creator: User): Task {
    const newTask: Task = {
      id: `YUKTI-${Math.floor(100 + Math.random() * 900)}`,
      title: taskData.title?.trim() || 'Untitled Task',
      description: taskData.description?.trim() || '',
      status: taskData.status || 'BACKLOG',
      priority: taskData.priority || 'P1',
      assignee: taskData.assignee || creator,
      updatedAt: 'Just now',
    }

    this.state.tasks = [newTask, ...this.state.tasks]
    this.saveToStorage()
    return newTask
  }

  public updateTaskStatus(taskId: string, newStatus: TaskStatus): Task | null {
    const task = this.state.tasks.find((t) => t.id === taskId)
    if (!task) return null

    task.status = newStatus
    task.updatedAt = 'Just now'
    if (newStatus !== 'BLOCKED') {
      task.waitingOn = undefined
    }

    this.state.tasks = [...this.state.tasks]
    this.saveToStorage()
    return task
  }

  public getMessages(channelId?: string): ChatMessage[] {
    if (!channelId) return [...this.state.messages]
    return this.state.messages.filter((m) => m.channelId === channelId)
  }

  public postMessage(channelId: string, content: string, author: User): { message: ChatMessage; proposal?: AIProposal } {
    const lower = content.toLowerCase()
    const isPotentialBlocker = 
      lower.includes('blocked') || 
      lower.includes('blocking') || 
      lower.includes('waiting on') || 
      lower.includes('pending') ||
      lower.includes('nahi mila') ||
      lower.includes('stuck') ||
      lower.includes('dependency issue')

    // Find if there's an in-progress or relevant task
    const activeTask = this.state.tasks.find((t) => t.status === 'IN_PROGRESS') || this.state.tasks[0]

    const newMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      channelId,
      author,
      content,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      isHinglish: lower.includes('nahi') || lower.includes('kya') || lower.includes('bhai') || lower.includes('mila'),
      extractedBlocker: isPotentialBlocker && activeTask
        ? {
            taskId: activeTask.id,
            reason: `Potential blocker signal detected in #${channelId}`,
            severity: 'P0',
          }
        : undefined,
    }

    this.state.messages = [...this.state.messages, newMsg]

    let newProposal: AIProposal | undefined
    if (isPotentialBlocker && activeTask && !this.state.proposals.some((p) => p.taskId === activeTask.id && p.status === 'PENDING')) {
      newProposal = {
        id: `prop-${Date.now()}`,
        taskId: activeTask.id,
        taskTitle: activeTask.title,
        proposedStatus: 'BLOCKED',
        reason: `Conversation signal in #${channelId}: "${content.slice(0, 80)}"`,
        evidenceMessage: {
          authorName: author.name,
          authorHandle: author.handle,
          channel: `#${channelId}`,
          timestamp: newMsg.timestamp,
          quote: content,
        },
        confidence: Math.max(this.state.settings.aiSensitivity, 88),
        suggestedAction: `Review dependency and verify with task assignee (@${activeTask.assignee.handle}).`,
        status: 'PENDING',
      }
      this.state.proposals = [newProposal, ...this.state.proposals]
    }

    this.saveToStorage()
    return { message: newMsg, proposal: newProposal }
  }

  public flagBlockerManually(message: ChatMessage): AIProposal | null {
    const activeTask = this.state.tasks.find((t) => t.status === 'IN_PROGRESS') || this.state.tasks[0]
    if (!activeTask) return null

    const proposal: AIProposal = {
      id: `prop-${Date.now()}`,
      taskId: activeTask.id,
      taskTitle: activeTask.title,
      proposedStatus: 'BLOCKED',
      reason: `Manual blocker escalation from #${message.channelId} by ${message.author.name}`,
      evidenceMessage: {
        authorName: message.author.name,
        authorHandle: message.author.handle,
        channel: `#${message.channelId}`,
        timestamp: message.timestamp,
        quote: message.content,
      },
      confidence: 100,
      suggestedAction: 'Human escalation requesting prompt lead intervention.',
      status: 'PENDING',
    }

    this.state.proposals = [proposal, ...this.state.proposals]
    this.saveToStorage()
    return proposal
  }

  public getProposals(): AIProposal[] {
    return [...this.state.proposals]
  }

  public approveProposal(proposalId: string, reviewer: User): { proposal: AIProposal; updatedTask?: Task } | null {
    const proposal = this.state.proposals.find((p) => p.id === proposalId)
    if (!proposal) return null

    proposal.status = 'APPROVED'
    proposal.reviewedAt = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

    const task = this.state.tasks.find((t) => t.id === proposal.taskId)
    if (task) {
      task.status = proposal.proposedStatus
      task.waitingOn = proposal.reason
      task.evidenceSnippet = proposal.evidenceMessage.quote
      task.updatedAt = 'Just now'
    }

    // Write audit notice to #blockers channel
    const auditNotice: ChatMessage = {
      id: `audit-${Date.now()}`,
      channelId: 'blockers',
      author: reviewer,
      content: `[AUDIT NOTICE] Task ${proposal.taskId} approved as ${proposal.proposedStatus} by ${reviewer.name}. Reason: ${proposal.reason}.`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }
    this.state.messages = [...this.state.messages, auditNotice]

    this.saveToStorage()
    return { proposal, updatedTask: task }
  }

  public rejectProposal(proposalId: string, reviewer: User, reason?: string): AIProposal | null {
    const proposal = this.state.proposals.find((p) => p.id === proposalId)
    if (!proposal) return null

    proposal.status = 'REJECTED'
    proposal.reviewedAt = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    if (reason) {
      proposal.suggestedAction = `Rejected by ${reviewer.name}: ${reason}`
    }

    this.saveToStorage()
    return proposal
  }

  public getGitEvents(): GitEvent[] {
    return [...this.state.gitEvents]
  }

  public recordGitEvent(eventData?: Partial<GitEvent>): GitEvent {
    const defaultSha = Math.random().toString(16).substring(2, 9)
    const activeTask = this.state.tasks[0]
    const repo = this.state.settings.repoName || 'org/repo'
    const newEvent: GitEvent = {
      id: `git-${Date.now()}`,
      type: eventData?.type || 'COMMIT',
      title: eventData?.title || `chore(core): push verification to ${eventData?.branch || 'main'}`,
      author: eventData?.author || this.state.currentUser.handle,
      avatar: eventData?.avatar || this.state.currentUser.avatar,
      branch: eventData?.branch || 'main',
      sha: eventData?.sha || defaultSha,
      timestamp: 'Just now',
      prStatus: eventData?.prStatus,
      linkedTaskId: eventData?.linkedTaskId || (activeTask ? activeTask.id : undefined),
      isEvidenceVerified: eventData?.isEvidenceVerified ?? true,
      url: eventData?.url || `https://github.com/${repo}/commit/${defaultSha}`,
    }
    this.state.gitEvents = [newEvent, ...this.state.gitEvents]
    this.saveToStorage()
    return newEvent
  }

  public getSettings(): WorkspaceSettings {
    return { ...this.state.settings }
  }

  public updateSettings(newSettings: Partial<WorkspaceSettings>): WorkspaceSettings {
    this.state.settings = { ...this.state.settings, ...newSettings }
    this.saveToStorage()
    return { ...this.state.settings }
  }

  public generateApiToken(): string {
    const randPart = Array.from({ length: 4 }, () => Math.random().toString(36).substring(2, 8)).join('_')
    const token = `yukti_live_${randPart}`
    this.updateSettings({ apiAccessToken: token })
    return token
  }

  public clearAllData(): void {
    this.state = {
      currentUser: this.state.currentUser,
      tasks: [],
      messages: [],
      proposals: [],
      gitEvents: [],
      settings: { ...DEFAULT_SETTINGS, apiAccessToken: this.state.settings.apiAccessToken },
      teamMembers: [this.state.currentUser],
    }
    this.saveToStorage()
  }

  public getProjectStats(): ProjectStats {
    const total = this.state.tasks.length
    const completed = this.state.tasks.filter((t) => t.status === 'DONE').length
    const blocked = this.state.tasks.filter((t) => t.status === 'BLOCKED').length
    const inProgress = this.state.tasks.filter((t) => t.status === 'IN_PROGRESS').length
    const pending = this.state.proposals.filter((p) => p.status === 'PENDING').length

    return {
      totalTasks: total,
      completedTasks: completed,
      blockedTasks: blocked,
      inProgressTasks: inProgress,
      pendingDecisions: pending,
      activeSprint: this.state.settings.activeSprint,
      repoConnected: this.state.settings.repoConnected,
      repoName: this.state.settings.repoName,
    }
  }
}
