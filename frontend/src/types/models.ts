import type { User } from './auth'

export type TaskStatus = 'BACKLOG' | 'IN_PROGRESS' | 'BLOCKED' | 'DONE'
export type TaskPriority = 'P0' | 'P1' | 'P2'

export interface GitHubRef {
  number: number
  title: string
  url: string
  status: 'OPEN' | 'MERGED' | 'IN_REVIEW' | 'CHANGES_REQUESTED'
  branch: string
}

export interface Task {
  id: string
  title: string
  description: string
  status: TaskStatus
  priority: TaskPriority
  assignee: User
  waitingOn?: string
  githubPr?: GitHubRef
  githubCommit?: string
  evidenceMessageId?: string
  evidenceSnippet?: string
  updatedAt: string
}

export interface ChatMessage {
  id: string
  channelId: string
  author: User
  content: string
  timestamp: string
  isHinglish?: boolean
  extractedBlocker?: {
    taskId: string
    reason: string
    severity: 'P0' | 'P1' | 'P2'
  }
}

export type ProposalStatus = 'PENDING' | 'APPROVED' | 'REJECTED'

export interface AIProposal {
  id: string
  taskId: string
  taskTitle: string
  proposedStatus: TaskStatus
  reason: string
  evidenceMessage: {
    authorName: string
    authorHandle: string
    channel: string
    timestamp: string
    quote: string
  }
  confidence?: number // Documented backend confidence only
  suggestedAction: string
  status: ProposalStatus
  reviewedAt?: string
}

export interface GitEvent {
  id: string
  type: 'PR' | 'COMMIT'
  title: string
  sha?: string
  author: string
  avatar?: string
  branch: string
  url: string
  timestamp: string
  prStatus?: 'OPEN' | 'MERGED' | 'IN_REVIEW'
  linkedTaskId?: string
  isEvidenceVerified?: boolean
}

export interface ProjectStats {
  totalTasks: number
  completedTasks: number
  blockedTasks: number
  inProgressTasks: number
  pendingDecisions: number
  activeSprint: string
  repoConnected: boolean
  repoName: string
}
