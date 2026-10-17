import React, { useState } from 'react'
import { 
  Hash, 
  Send, 
  AlertTriangle, 
  PlusCircle, 
  ShieldAlert, 
  ShieldCheck
} from 'lucide-react'
import type { ChatMessage } from '../../types/models'
import type { User } from '../../types/auth'

interface TeamChatProps {
  currentUser: User
  messages: ChatMessage[]
  onSendMessage: (channelId: string, content: string) => void
  onFlagBlocker: (message: ChatMessage) => void
  onCreateTaskFromMessage: (message: ChatMessage) => void
  activeChannel: string
  onSelectChannel?: (channelId: string) => void
}

const CHANNELS = [
  { id: 'general', name: 'general', desc: 'Team-wide announcements & standup' },
  { id: 'frontend', name: 'frontend', desc: 'UI architecture, design tokens & client state' },
  { id: 'backend', name: 'backend', desc: 'FastAPI endpoints, PostgreSQL schema & webhooks' },
  { id: 'blockers', name: 'blockers', desc: 'Official blocker resolutions and system alerts' },
]

export const TeamChat: React.FC<TeamChatProps> = ({
  currentUser,
  messages,
  onSendMessage,
  onFlagBlocker,
  onCreateTaskFromMessage,
  activeChannel,
}) => {
  const [inputText, setInputText] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const currentChannelInfo = CHANNELS.find((c) => c.id === activeChannel) || CHANNELS[0]
  const channelMessages = messages.filter((m) => m.channelId === activeChannel)

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputText.trim() || isSubmitting) return

    setIsSubmitting(true)
    onSendMessage(activeChannel, inputText.trim())
    setInputText('')
    setIsSubmitting(false)
  }

  return (
    <div className="h-full flex flex-col bg-[#090D16]">
      {/* Channel Top Header */}
      <div className="h-14 px-4 sm:px-6 border-b border-[#263246] flex items-center justify-between bg-[#111925] shrink-0">
        <div className="flex items-center gap-2">
          <Hash className="w-4 h-4 text-[#77869B]" />
          <span className="font-semibold text-[#F1F5F9] text-sm sm:text-base">{currentChannelInfo.name}</span>
          <span className="text-xs text-[#77869B] border-l border-[#263246] pl-2.5 ml-1 hidden sm:inline font-sans">
            {currentChannelInfo.desc}
          </span>
        </div>

        {/* Channel Status Info */}
        <div className="flex items-center gap-2 text-xs font-sans text-[#77869B]">
          <span className="hidden sm:inline">Channel Sync</span>
          <span className="px-2 py-0.5 rounded bg-[#161F2D] text-[#38B982] border border-[#263246] font-medium text-[11px]">
            Connected
          </span>
        </div>
      </div>

      {/* Messages List Area */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
        {channelMessages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center text-[#77869B] p-6">
            {activeChannel === 'blockers' ? (
              <div className="max-w-md space-y-2">
                <div className="w-12 h-12 rounded-xl bg-[#111925] border border-[#263246] flex items-center justify-center text-[#38B982] mx-auto mb-3">
                  <ShieldCheck className="w-6 h-6" />
                </div>
                <h3 className="text-base font-semibold text-[#F1F5F9] font-sans">Blocker Resolution Channel</h3>
                <p className="text-xs text-[#A0AEC0] leading-relaxed font-sans">
                  Official blocker decisions and audit notices are dispatched here once approved in the Admin Inbox. There are currently no active blocker alerts in this sprint.
                </p>
              </div>
            ) : (
              <div className="max-w-md space-y-2">
                <Hash className="w-10 h-10 text-[#263246] mx-auto mb-2" />
                <h3 className="text-base font-semibold text-[#F1F5F9] font-sans">Welcome to #{currentChannelInfo.name}</h3>
                <p className="text-xs text-[#A0AEC0] leading-relaxed font-sans">
                  Start of discussion for #{currentChannelInfo.name}. Team discussions here are continuously grounded against active sprint tasks.
                </p>
              </div>
            )}
          </div>
        ) : (
          channelMessages.map((msg) => (
            <div
              key={msg.id}
              className="group relative flex items-start gap-3 hover:bg-[#111925]/70 -mx-3 sm:-mx-4 px-3 sm:px-4 py-2 rounded-lg transition-colors"
            >
              {/* Avatar */}
              <img
                src={msg.author.avatar}
                alt={msg.author.name}
                className="w-8 h-8 rounded-full object-cover shrink-0 border border-[#263246] mt-0.5"
              />

              {/* Message Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-baseline gap-2 mb-1">
                  <span className="font-semibold text-[#F1F5F9] text-xs sm:text-sm hover:underline cursor-pointer font-sans">
                    {msg.author.name}
                  </span>
                  <span className="text-[10px] px-2 py-0.5 rounded font-sans font-medium bg-[#161F2D] text-[#A0AEC0] border border-[#263246]">
                    {msg.author.role === 'ADMIN' ? 'Lead' : 'Developer'}
                  </span>
                  <span className="text-[10px] text-[#77869B] font-mono">
                    {msg.timestamp}
                  </span>
                </div>

                {/* Message body */}
                <p className="text-xs sm:text-sm text-[#F1F5F9] leading-relaxed break-words font-sans">
                  {msg.content}
                </p>

                {/* AI Blocker Tag Banner if extracted */}
                {msg.extractedBlocker && (
                  <div className="mt-2.5 inline-flex items-center gap-2 p-2 rounded-lg bg-[#161F2D] border border-[#E47777]/30 text-xs">
                    <AlertTriangle className="w-3.5 h-3.5 text-[#E47777] shrink-0" />
                    <div>
                      <span className="font-semibold text-[#E47777]">AI Detected Blocker: </span>
                      <span className="text-[#F1F5F9] font-medium">Mapped to task {msg.extractedBlocker.taskId}</span>
                      <span className="mx-1 text-[#77869B]">·</span>
                      <span className="text-[#E5B85C] font-mono text-[11px]">Forwarded to Admin Inbox</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Hover Actions Bar */}
              <div className="absolute right-3 top-2 opacity-0 group-hover:opacity-100 transition-opacity flex items-center bg-[#161F2D] border border-[#263246] rounded-md shadow-md overflow-hidden">
                <button
                  onClick={() => onFlagBlocker(msg)}
                  className="p-1 hover:bg-[#263246] text-[#E5B85C] text-xs flex items-center gap-1 px-2 transition-colors"
                  title="Flag as blocker for lead review"
                >
                  <ShieldAlert className="w-3 h-3" />
                  <span className="font-mono text-[10px]">Flag</span>
                </button>
                <div className="w-[1px] h-3.5 bg-[#263246]" />
                <button
                  onClick={() => onCreateTaskFromMessage(msg)}
                  className="p-1 hover:bg-[#263246] text-[#F1F5F9] text-xs flex items-center gap-1 px-2 transition-colors"
                  title="Create task from this message"
                >
                  <PlusCircle className="w-3 h-3 text-[#62CBE8]" />
                  <span className="font-mono text-[10px]">New Task</span>
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Input Bar */}
      <div className="p-3 sm:p-4 bg-[#111925] border-t border-[#263246]">
        <form onSubmit={handleSend} className="relative bg-[#161F2D] border border-[#263246] focus-within:border-[#62CBE8]/60 rounded-xl transition-colors">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder={`Message #${currentChannelInfo.name} (Accepts English or Hinglish)...`}
            className="w-full bg-transparent text-xs sm:text-sm text-[#F1F5F9] placeholder-[#77869B] px-3.5 py-2.5 outline-none pr-11 font-sans"
          />
          <button
            type="submit"
            disabled={!inputText.trim() || isSubmitting}
            className="absolute right-2 top-2 p-1.5 bg-[#62CBE8] hover:bg-[#79D6EE] disabled:opacity-30 disabled:hover:bg-[#62CBE8] text-[#07131C] font-semibold rounded-lg transition-all"
            title="Send message"
          >
            <Send className="w-3.5 h-3.5" />
          </button>
        </form>
        <div className="flex items-center justify-between text-[10px] text-[#77869B] font-mono mt-1.5 px-1">
          <span>YuktiOps AI parses intent, tasks &amp; blockers automatically.</span>
          <span>Logged in: {currentUser.name} ({currentUser.role})</span>
        </div>
      </div>
    </div>
  )
}

export default TeamChat
