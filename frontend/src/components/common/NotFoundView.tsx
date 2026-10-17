import React from 'react'
import { Terminal, ArrowLeft, Activity } from 'lucide-react'

interface NotFoundViewProps {
  onGoToDashboard: () => void
  onGoToLanding: () => void
}

export const NotFoundView: React.FC<NotFoundViewProps> = ({
  onGoToDashboard,
  onGoToLanding,
}) => {
  return (
    <div className="h-screen w-screen bg-[#090D18] flex flex-col items-center justify-center p-6 text-center text-[#E7EDF7]">
      <div className="w-16 h-16 rounded-2xl bg-[#121824] border border-[#202B3F] flex items-center justify-center text-[#65D8FF] mb-6 shadow-2xl">
        <Terminal className="w-8 h-8" />
      </div>

      <div className="text-xs font-mono px-3 py-1 rounded-full bg-[#151C2B] text-[#65D8FF] border border-[#65D8FF]/30 mb-3">
        HTTP 404 · ROUTE UNRESOLVED
      </div>

      <h1 className="font-display text-3xl font-bold text-white mb-2">
        Coordinates Not Found
      </h1>

      <p className="max-w-md text-sm text-[#8292AB] mb-6 leading-relaxed font-sans">
        The requested screen coordinate does not exist in this YuktiOps workspace or has been moved to another sprint.
      </p>

      <div className="flex items-center gap-3">
        <button
          onClick={onGoToDashboard}
          className="px-5 py-2.5 bg-[#65D8FF] hover:bg-[#52c8ef] text-[#090D18] font-bold text-xs rounded-xl flex items-center gap-2 transition-colors font-mono"
        >
          <Activity className="w-4 h-4" />
          <span>Open Command Center</span>
        </button>

        <button
          onClick={onGoToLanding}
          className="px-5 py-2.5 bg-[#151C2B] hover:bg-[#1A2335] text-white border border-[#202B3F] text-xs font-semibold rounded-xl flex items-center gap-2 transition-colors font-mono"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Return Home</span>
        </button>
      </div>
    </div>
  )
}

export default NotFoundView
