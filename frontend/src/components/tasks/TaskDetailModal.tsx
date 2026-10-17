import React from 'react'
import { X, GitPullRequest, MessageSquare, AlertTriangle } from 'lucide-react'
import type { Task } from '../../types/models'

interface TaskDetailModalProps {
  task: Task | null
  onClose: () => void
}

export const TaskDetailModal: React.FC<TaskDetailModalProps> = ({ task, onClose }) => {
  if (!task) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#090D16]/80 backdrop-blur-xs p-4">
      <div className="w-full max-w-xl bg-[#111925] border border-[#263246] rounded-xl shadow-2xl overflow-hidden">
        {/* Top Header */}
        <div className="px-5 py-3.5 border-b border-[#263246] flex items-center justify-between bg-[#161F2D]">
          <div className="flex items-center gap-2.5">
            <span className="font-mono text-xs font-semibold text-[#62CBE8]">{task.id}</span>
            <span
              className={`text-[10px] font-sans font-semibold px-2 py-0.5 rounded border ${
                task.status === 'BLOCKED'
                  ? 'bg-[#E47777]/15 text-[#E47777] border-[#E47777]/30'
                  : task.status === 'DONE'
                  ? 'bg-[#38B982]/15 text-[#38B982] border-[#38B982]/30'
                  : 'bg-[#62CBE8]/15 text-[#62CBE8] border-[#62CBE8]/30'
              }`}
            >
              {task.status}
            </span>
          </div>
          <button onClick={onClose} className="text-[#77869B] hover:text-[#F1F5F9] transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-5 space-y-4 max-h-[80vh] overflow-y-auto">
          <div>
            <h3 className="text-base font-semibold text-[#F1F5F9] mb-1.5 font-sans">{task.title}</h3>
            <p className="text-xs text-[#A0AEC0] leading-relaxed font-sans">{task.description}</p>
          </div>

          {/* Dependency Banner */}
          {task.waitingOn && (
            <div className="p-3 bg-[#161F2D] border border-[#E47777]/30 rounded-lg text-xs text-[#E47777] font-sans">
              <div className="flex items-center gap-1.5 font-semibold mb-1">
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>Blocker Dependency</span>
              </div>
              <p className="text-[#F1F5F9]">{task.waitingOn}</p>
            </div>
          )}

          {/* Chat Evidence */}
          {task.evidenceSnippet && (
            <div className="p-3 bg-[#161F2D] border border-[#263246] rounded-lg text-xs font-sans">
              <div className="flex items-center gap-1.5 text-[#62CBE8] font-semibold mb-1.5">
                <MessageSquare className="w-3.5 h-3.5" />
                <span>Linked Conversation Evidence</span>
              </div>
              <blockquote className="font-mono text-[#E5B85C] bg-[#090D16] p-2.5 rounded border border-[#263246]">
                &quot;{task.evidenceSnippet}&quot;
              </blockquote>
            </div>
          )}

          {/* Linked GitHub Activity */}
          {task.githubPr && (
            <div className="p-3 bg-[#161F2D] border border-[#263246] rounded-lg text-xs font-sans">
              <div className="flex items-center gap-1.5 text-[#38B982] font-semibold mb-1.5">
                <GitPullRequest className="w-3.5 h-3.5" />
                <span>Associated Pull Request</span>
              </div>
              <div className="flex items-center justify-between bg-[#090D16] p-2.5 rounded border border-[#263246]">
                <div>
                  <div className="font-medium text-[#F1F5F9] text-xs">PR #{task.githubPr.number}: {task.githubPr.title}</div>
                  <div className="text-[10px] text-[#77869B] font-mono">Branch: {task.githubPr.branch}</div>
                </div>
                <span className="text-[10px] font-sans font-semibold px-2 py-0.5 rounded bg-[#38B982]/15 text-[#38B982] border border-[#38B982]/30">
                  {task.githubPr.status}
                </span>
              </div>
            </div>
          )}

          {/* Metadata Grid */}
          <div className="grid grid-cols-2 gap-3 pt-3 border-t border-[#263246] text-xs font-sans">
            <div>
              <span className="text-[#77869B] block mb-1 text-[11px] font-medium">Assignee</span>
              <div className="flex items-center gap-2">
                <img
                  src={task.assignee.avatar}
                  alt={task.assignee.name}
                  className="w-5 h-5 rounded-full object-cover border border-[#263246]"
                />
                <span className="text-[#F1F5F9] font-medium">{task.assignee.name}</span>
              </div>
            </div>
            <div>
              <span className="text-[#77869B] block mb-1 text-[11px] font-medium">Priority</span>
              <span className="font-mono font-semibold text-[#F1F5F9] text-xs">{task.priority}</span>
            </div>
          </div>
        </div>

        <div className="px-5 py-3 bg-[#161F2D] border-t border-[#263246] flex justify-end">
          <button
            onClick={onClose}
            className="px-3.5 py-1.5 bg-[#090D16] hover:bg-[#263246] text-xs font-medium text-[#F1F5F9] rounded-lg border border-[#263246] transition-colors font-sans"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}

export default TaskDetailModal
