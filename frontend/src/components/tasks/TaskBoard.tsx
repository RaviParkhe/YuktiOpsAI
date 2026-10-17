import React, { useState } from 'react'
import { 
  Kanban, 
  Plus, 
  GitPullRequest, 
  AlertTriangle, 
  MessageSquare, 
  Filter
} from 'lucide-react'
import type { Task, TaskStatus } from '../../types/models'
import type { UserRole } from '../../types/auth'

interface TaskBoardProps {
  userRole?: UserRole
  tasks: Task[]
  onUpdateTaskStatus: (taskId: string, newStatus: TaskStatus) => void
  onOpenCreateTaskModal: () => void
  onSelectTask: (task: Task) => void
}

const COLUMNS: { id: TaskStatus; label: string; borderAccent: string }[] = [
  { id: 'BACKLOG', label: 'Backlog', borderAccent: 'border-b-[#77869B]' },
  { id: 'IN_PROGRESS', label: 'In Progress', borderAccent: 'border-b-[#62CBE8]' },
  { id: 'BLOCKED', label: 'Blocked / Waiting', borderAccent: 'border-b-[#E47777]' },
  { id: 'DONE', label: 'Done & Shipped', borderAccent: 'border-b-[#38B982]' },
]

export const TaskBoard: React.FC<TaskBoardProps> = ({
  userRole: _userRole,
  tasks,
  onUpdateTaskStatus,
  onOpenCreateTaskModal,
  onSelectTask,
}) => {
  const [filterPriority, setFilterPriority] = useState<string>('ALL')

  const filteredTasks = tasks.filter((t) => {
    if (filterPriority === 'ALL') return true
    return t.priority === filterPriority
  })

  return (
    <div className="h-full flex flex-col bg-[#090D16] overflow-hidden">
      {/* Top Action Bar */}
      <div className="h-14 px-4 sm:px-6 border-b border-[#263246] flex items-center justify-between bg-[#111925] shrink-0">
        <div className="flex items-center gap-3">
          <Kanban className="w-4 h-4 text-[#62CBE8]" />
          <h1 className="text-base sm:text-lg font-normal text-[#F1F5F9] font-display tracking-wide">Project Task Board</h1>
          <span className="text-xs font-sans px-2.5 py-0.5 rounded-full bg-[#161F2D] text-[#A0AEC0] border border-[#263246]">
            {tasks.length} {tasks.length === 1 ? 'task' : 'tasks'}
          </span>
        </div>

        <div className="flex items-center gap-2.5">
          {/* Priority filter */}
          <div className="flex items-center gap-1.5 bg-[#161F2D] px-2.5 py-1.5 rounded-lg border border-[#263246] text-xs">
            <Filter className="w-3.5 h-3.5 text-[#77869B]" />
            <select
              value={filterPriority}
              onChange={(e) => setFilterPriority(e.target.value)}
              className="bg-transparent text-[#F1F5F9] outline-none cursor-pointer font-sans text-xs"
            >
              <option value="ALL" className="bg-[#161F2D]">All Priorities</option>
              <option value="P0" className="bg-[#161F2D]">P0 - Blocker</option>
              <option value="P1" className="bg-[#161F2D]">P1 - High</option>
              <option value="P2" className="bg-[#161F2D]">P2 - Standard</option>
            </select>
          </div>

          <button
            onClick={onOpenCreateTaskModal}
            className="px-3.5 py-1.5 bg-[#62CBE8] hover:bg-[#79D6EE] text-[#07131C] text-xs font-semibold rounded-lg flex items-center gap-1.5 shadow-xs transition-colors font-sans"
          >
            <Plus className="w-4 h-4" />
            <span>Create Task</span>
          </button>
        </div>
      </div>

      {/* Board Columns Grid */}
      <div className="flex-1 overflow-x-auto p-4 sm:p-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 h-full min-w-[960px]">
          {COLUMNS.map((col) => {
            const colTasks = filteredTasks.filter((t) => t.status === col.id)
            return (
              <div
                key={col.id}
                className="flex flex-col bg-[#111925] rounded-xl border border-[#263246] overflow-hidden"
              >
                {/* Column Header */}
                <div className={`p-3 bg-[#161F2D] border-b-2 ${col.borderAccent} flex items-center justify-between`}>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-xs text-[#F1F5F9] font-sans">
                      {col.label}
                    </span>
                    <span className="text-[10px] font-sans px-2 py-0.5 rounded-full bg-[#090D16] border border-[#263246] text-[#A0AEC0] font-medium">
                      {colTasks.length}
                    </span>
                  </div>
                </div>

                {/* Task Cards Container */}
                <div className="flex-1 overflow-y-auto p-3 space-y-3">
                  {colTasks.length === 0 ? (
                    <div className="p-6 text-center text-xs text-[#77869B] font-sans border border-dashed border-[#263246] rounded-lg space-y-2">
                      <p>No tasks in {col.label}</p>
                      {col.id === 'BACKLOG' && (
                        <button
                          onClick={onOpenCreateTaskModal}
                          className="px-2.5 py-1 bg-[#090D16] hover:bg-[#1E293B] text-[#62CBE8] hover:text-[#79D6EE] rounded text-[11px] font-sans font-medium inline-flex items-center gap-1 transition-colors border border-[#263246]"
                        >
                          <Plus className="w-3 h-3" />
                          <span>Add Task</span>
                        </button>
                      )}
                    </div>
                  ) : (
                    colTasks.map((task) => (
                      <div
                        key={task.id}
                        onClick={() => onSelectTask(task)}
                        className={`bg-[#161F2D] hover:bg-[#1D283A] border rounded-lg p-3.5 cursor-pointer shadow-xs transition-all hover:border-[#62CBE8]/50 ${
                          task.status === 'BLOCKED' ? 'border-[#E47777]/50' : 'border-[#263246]'
                        }`}
                      >
                        {/* Top ID & Priority */}
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-mono text-xs font-semibold text-[#62CBE8]">
                            {task.id}
                          </span>
                          <span
                            className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded ${
                              task.priority === 'P0'
                                ? 'bg-[#E47777]/20 text-[#E47777] border border-[#E47777]/40'
                                : task.priority === 'P1'
                                ? 'bg-[#E5B85C]/20 text-[#E5B85C] border border-[#E5B85C]/40'
                                : 'bg-[#090D16] text-[#A0AEC0] border border-[#263246]'
                            }`}
                          >
                            {task.priority}
                          </span>
                        </div>

                        {/* Title */}
                        <h4 className="text-xs font-medium text-[#F1F5F9] mb-2 line-clamp-2 leading-relaxed font-sans">
                          {task.title}
                        </h4>

                        {/* Dependency Banner if Blocked */}
                        {task.waitingOn && (
                          <div className="mb-2.5 p-2 rounded bg-[#090D16] border border-[#E47777]/30 text-[11px] text-[#E47777] flex items-start gap-1.5 font-sans">
                            <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5 text-[#E47777]" />
                            <div>
                              <span className="font-semibold">Waiting: </span>
                              <span>{task.waitingOn}</span>
                            </div>
                          </div>
                        )}

                        {/* Attached Evidence Snippet */}
                        {task.evidenceSnippet && (
                          <div className="mb-2.5 p-2 rounded bg-[#090D16] border border-[#263246] text-[11px] font-mono text-[#E5B85C] flex items-start gap-1.5">
                            <MessageSquare className="w-3.5 h-3.5 text-[#62CBE8] shrink-0 mt-0.5" />
                            <div className="line-clamp-2">
                              &quot;{task.evidenceSnippet}&quot;
                            </div>
                          </div>
                        )}

                        {/* GitHub PR link if attached */}
                        {task.githubPr && (
                          <div className="mb-2.5 flex items-center gap-1.5 text-[11px] font-mono px-2 py-1 bg-[#090D16] border border-[#263246] rounded text-[#A0AEC0]">
                            <GitPullRequest className="w-3.5 h-3.5 text-[#38B982]" />
                            <span className="text-[#F1F5F9] font-medium">PR #{task.githubPr.number}</span>
                            <span className="text-[10px] text-[#38B982] font-semibold">({task.githubPr.status})</span>
                          </div>
                        )}

                        {/* Bottom: Assignee & Quick Status Change */}
                        <div className="flex items-center justify-between pt-2 border-t border-[#263246] text-xs">
                          <div className="flex items-center gap-2">
                            <img
                              src={task.assignee.avatar}
                              alt={task.assignee.name}
                              className="w-5 h-5 rounded-full object-cover border border-[#263246]"
                            />
                            <span className="text-[11px] text-[#A0AEC0] truncate max-w-[80px] font-sans">
                              {task.assignee.name.split(' ')[0]}
                            </span>
                          </div>

                          {/* Quick Column Advance Button */}
                          <div className="flex items-center gap-1">
                            {task.status !== 'DONE' && (
                              <button
                                onClick={(e) => {
                                  e.stopPropagation()
                                  const nextStatus: Record<TaskStatus, TaskStatus> = {
                                    BACKLOG: 'IN_PROGRESS',
                                    IN_PROGRESS: 'DONE',
                                    BLOCKED: 'IN_PROGRESS',
                                    DONE: 'DONE',
                                  }
                                  onUpdateTaskStatus(task.id, nextStatus[task.status])
                                }}
                                className="px-2 py-0.5 bg-[#090D16] hover:bg-[#263246] text-[#F1F5F9] text-[11px] font-sans font-medium rounded border border-[#263246] transition-colors"
                                title="Advance task status"
                              >
                                Advance →
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export default TaskBoard
