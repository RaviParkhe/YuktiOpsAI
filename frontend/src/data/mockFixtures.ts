import type { Task, ChatMessage, AIProposal, GitEvent, ProjectStats } from '../types/models'
import type { User } from '../types/auth'

// Baseline empty fixtures - no fabricated business data
export const MOCK_USERS: Record<string, User> = {}

export const INITIAL_TASKS: Task[] = []

export const INITIAL_MESSAGES: ChatMessage[] = []

export const INITIAL_PROPOSALS: AIProposal[] = []

export const INITIAL_GIT_EVENTS: GitEvent[] = []

export const INITIAL_PROJECT_STATS: ProjectStats = {
  totalTasks: 0,
  completedTasks: 0,
  blockedTasks: 0,
  inProgressTasks: 0,
  pendingDecisions: 0,
  activeSprint: '',
  repoConnected: false,
  repoName: '',
}
