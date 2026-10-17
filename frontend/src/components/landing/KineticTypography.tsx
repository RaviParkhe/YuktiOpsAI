import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion'
import { MessageSquare, Layers, Kanban, CheckCircle2 } from 'lucide-react'

const PILLARS = [
  {
    word: 'Conversations',
    color: 'text-[#62CBE8]',
    border: 'border-[#62CBE8]/30',
    bg: 'bg-[#62CBE8]/10',
    icon: MessageSquare,
    desc: 'Informal English and Hinglish developer discussions ingested in real time.',
    tag: 'INPUT STREAM',
  },
  {
    word: 'Context',
    color: 'text-[#F1F5F9]',
    border: 'border-[#263246]',
    bg: 'bg-[#161F2D]',
    icon: Layers,
    desc: 'Historical architecture agreements, schema specifications & project memory.',
    tag: 'LAYERED MEMORY',
  },
  {
    word: 'Coordination',
    color: 'text-[#E5B85C]',
    border: 'border-[#E5B85C]/30',
    bg: 'bg-[#E5B85C]/10',
    icon: Kanban,
    desc: 'Automated blocker escalation, owner bandwidth radar & task state updates.',
    tag: 'ADMIN QUEUE',
  },
  {
    word: 'Execution',
    color: 'text-[#38B982]',
    border: 'border-[#38B982]/30',
    bg: 'bg-[#38B982]/10',
    icon: CheckCircle2,
    desc: 'Traceable GitHub PRs, verified criteria completion, and shipped features.',
    tag: 'PRODUCTION CODE',
  },
]

export const KineticTypography: React.FC = () => {
  const [index, setIndex] = useState(0)
  const shouldReduceMotion = useReducedMotion()

  useEffect(() => {
    if (shouldReduceMotion) return
    const interval = setInterval(() => {
      setIndex((prev) => (prev + 1) % PILLARS.length)
    }, 3200)
    return () => clearInterval(interval)
  }, [shouldReduceMotion])

  const current = PILLARS[index]
  const Icon = current.icon

  return (
    <div className="w-full max-w-3xl mx-auto py-6">
      <div className="bg-[#111925] border border-[#263246] rounded-2xl p-6 sm:p-8 shadow-xl relative overflow-hidden">
        <div className="absolute inset-0 tech-grid opacity-15 pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          {/* Left Title Label */}
          <div className="space-y-1">
            <span className="text-[11px] font-sans font-semibold uppercase tracking-widest text-[#A0AEC0] block">
              THE UNIFIED PIPELINE
            </span>
            <h3 className="font-display text-base sm:text-lg text-[#F1F5F9] tracking-wide font-normal">
              From Raw Thought To
            </h3>
          </div>

          {/* Center Dynamic Word Transition */}
          <div className="h-16 flex items-center min-w-[240px]">
            <AnimatePresence mode="wait">
              <motion.div
                key={current.word}
                initial={shouldReduceMotion ? { opacity: 1 } : { opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={shouldReduceMotion ? { opacity: 1 } : { opacity: 0, y: -15 }}
                transition={{ duration: 0.35, ease: 'easeOut' }}
                className="flex items-center gap-3"
              >
                <div className={`p-2.5 rounded-xl ${current.bg} border ${current.border} shrink-0`}>
                  <Icon className={`w-6 h-6 ${current.color}`} />
                </div>
                <div>
                  <span className={`text-lg sm:text-xl font-display tracking-wide font-normal ${current.color} block`}>
                    {current.word}
                  </span>
                  <span className="text-[10px] font-mono text-[#77869B] tracking-wider">
                    [{current.tag}]
                  </span>
                </div>
              </motion.div>
            </AnimatePresence>
          </div>
        </div>

        {/* Dynamic Sub-Description */}
        <div className="mt-6 pt-4 border-t border-[#263246] flex flex-col sm:flex-row sm:items-center justify-between gap-4 text-xs">
          <p className="text-[#A0AEC0] font-sans font-normal">
            {current.desc}
          </p>

          <div className="flex items-center gap-1.5 shrink-0">
            {PILLARS.map((p, idx) => (
              <button
                key={p.word}
                onClick={() => setIndex(idx)}
                className={`h-1.5 rounded-full transition-all ${
                  idx === index
                    ? 'w-6 bg-[#62CBE8]'
                    : 'w-2 bg-[#263246] hover:bg-slate-600'
                }`}
                title={`Switch to ${p.word}`}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default KineticTypography
