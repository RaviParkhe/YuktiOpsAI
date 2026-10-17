import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { CheckCircle2, AlertCircle, Info, AlertTriangle, X } from 'lucide-react'

export type ToastType = 'success' | 'error' | 'info' | 'warning'

export interface ToastMessage {
  id: string
  title: string
  description?: string
  type: ToastType
}

interface ToastContainerProps {
  toasts: ToastMessage[]
  onDismiss: (id: string) => void
}

export const ToastContainer: React.FC<ToastContainerProps> = ({ toasts, onDismiss }) => {
  return (
    <div 
      className="fixed bottom-5 right-5 z-50 flex flex-col gap-2.5 max-w-sm w-full pointer-events-none"
      aria-live="polite"
    >
      <AnimatePresence>
        {toasts.map((toast) => (
          <motion.div
            key={toast.id}
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 15, scale: 0.95 }}
            transition={{ duration: 0.25 }}
            className={`pointer-events-auto p-4 rounded-xl border shadow-2xl flex items-start gap-3 bg-[#121824] backdrop-blur-md ${
              toast.type === 'success'
                ? 'border-[#23A55A]/50 text-white'
                : toast.type === 'error'
                ? 'border-[#ED4245]/50 text-white'
                : toast.type === 'warning'
                ? 'border-[#FEE75C]/50 text-white'
                : 'border-[#65D8FF]/50 text-white'
            }`}
          >
            <div className="shrink-0 mt-0.5">
              {toast.type === 'success' && <CheckCircle2 className="w-5 h-5 text-[#23A55A]" />}
              {toast.type === 'error' && <AlertCircle className="w-5 h-5 text-[#ED4245]" />}
              {toast.type === 'warning' && <AlertTriangle className="w-5 h-5 text-[#FEE75C]" />}
              {toast.type === 'info' && <Info className="w-5 h-5 text-[#65D8FF]" />}
            </div>

            <div className="flex-1 min-w-0">
              <h5 className="text-xs font-bold leading-tight font-sans text-white">{toast.title}</h5>
              {toast.description && (
                <p className="text-[11px] text-[#8292AB] mt-1 font-sans leading-relaxed">
                  {toast.description}
                </p>
              )}
            </div>

            <button
              onClick={() => onDismiss(toast.id)}
              className="text-[#8292AB] hover:text-white transition-colors shrink-0 p-0.5"
            >
              <X className="w-4 h-4" />
            </button>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  )
}

export default ToastContainer
