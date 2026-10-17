import React, { useState } from 'react'
import { X } from 'lucide-react'
import type { Task, TaskPriority } from '../../types/models'
import type { User } from '../../types/auth'

interface CreateTaskModalProps {
  isOpen: boolean
  onClose: () => void
  onCreateTask: (newTask: Partial<Task>) => void
  initialTitle?: string
  currentUser: User
  teamMembers?: User[]
}

export const CreateTaskModal: React.FC<CreateTaskModalProps> = ({
  isOpen,
  onClose,
  onCreateTask,
  initialTitle = '',
  currentUser,
  teamMembers = [],
}) => {
  const [title, setTitle] = useState(initialTitle)
  const [description, setDescription] = useState('')
  const [priority, setPriority] = useState<TaskPriority>('P1')
  const [selectedAssigneeId, setSelectedAssigneeId] = useState<string>(currentUser.id)

  if (!isOpen) return null

  // Collect available assignees without fictional duplicates
  const availableAssignees = teamMembers.length > 0 
    ? teamMembers 
    : [currentUser]

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim()) return

    const chosenAssignee = availableAssignees.find((m) => m.id === selectedAssigneeId) || currentUser

    onCreateTask({
      id: `YUKTI-${Math.floor(100 + Math.random() * 900)}`,
      title: title.trim(),
      description: description.trim(),
      status: 'BACKLOG',
      priority,
      assignee: chosenAssignee,
      updatedAt: 'Just now',
    })
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#090D16]/80 backdrop-blur-xs p-4">
      <div className="w-full max-w-lg bg-[#111925] border border-[#263246] rounded-xl shadow-2xl overflow-hidden">
        <div className="px-5 py-3.5 border-b border-[#263246] flex items-center justify-between bg-[#161F2D]">
          <h3 className="text-sm font-semibold text-[#F1F5F9] font-sans">Create New Project Task</h3>
          <button onClick={onClose} className="text-[#77869B] hover:text-[#F1F5F9] transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div>
            <label className="block text-[11px] font-semibold text-[#A0AEC0] uppercase tracking-wider mb-1 font-sans">
              Task Title
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              placeholder="e.g. Implement Webhook Authentication Handler"
              className="w-full bg-[#161F2D] border border-[#263246] focus:border-[#62CBE8] rounded-lg px-3 py-2 text-xs sm:text-sm text-[#F1F5F9] placeholder-[#77869B] outline-none transition-colors font-sans"
            />
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-[#A0AEC0] uppercase tracking-wider mb-1 font-sans">
              Description / Acceptance Criteria
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              placeholder="Provide clear technical scope and constraints..."
              className="w-full bg-[#161F2D] border border-[#263246] focus:border-[#62CBE8] rounded-lg px-3 py-2 text-xs sm:text-sm text-[#F1F5F9] placeholder-[#77869B] outline-none transition-colors font-sans"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-semibold text-[#A0AEC0] uppercase tracking-wider mb-1 font-sans">
                Priority
              </label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value as TaskPriority)}
                className="w-full bg-[#161F2D] border border-[#263246] focus:border-[#62CBE8] rounded-lg px-3 py-2 text-xs text-[#F1F5F9] outline-none font-sans"
              >
                <option value="P0" className="bg-[#161F2D]">P0 - Critical Blocker</option>
                <option value="P1" className="bg-[#161F2D]">P1 - High Priority</option>
                <option value="P2" className="bg-[#161F2D]">P2 - Normal</option>
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-[#A0AEC0] uppercase tracking-wider mb-1 font-sans">
                Assignee
              </label>
              <select
                value={selectedAssigneeId}
                onChange={(e) => setSelectedAssigneeId(e.target.value)}
                className="w-full bg-[#161F2D] border border-[#263246] focus:border-[#62CBE8] rounded-lg px-3 py-2 text-xs text-[#F1F5F9] outline-none font-sans"
              >
                {availableAssignees.map((member) => (
                  <option key={member.id} value={member.id} className="bg-[#161F2D]">
                    {member.name} {member.id === currentUser.id ? '(You)' : `(${member.role})`}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-[#263246]">
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-1.5 text-xs font-medium text-[#77869B] hover:text-[#F1F5F9] transition-colors font-sans"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-1.5 bg-[#62CBE8] hover:bg-[#79D6EE] text-[#07131C] text-xs font-semibold rounded-lg shadow-xs transition-colors font-sans"
            >
              Create Task
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default CreateTaskModal
