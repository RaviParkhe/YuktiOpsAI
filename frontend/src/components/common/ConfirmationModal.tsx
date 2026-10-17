import React from 'react'
import { AlertTriangle, X } from 'lucide-react'

interface ConfirmationModalProps {
  isOpen: boolean
  title: string
  description: string
  confirmLabel?: string
  cancelLabel?: string
  severity?: 'danger' | 'warning' | 'info'
  onConfirm: () => void
  onCancel: () => void
}

export const ConfirmationModal: React.FC<ConfirmationModalProps> = ({
  isOpen,
  title,
  description,
  confirmLabel = 'Confirm Action',
  cancelLabel = 'Cancel',
  severity = 'danger',
  onConfirm,
  onCancel,
}) => {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#090D18]/80 backdrop-blur-sm p-4">
      <div className="w-full max-w-md bg-[#121824] border border-[#202B3F] rounded-2xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        <div className="px-6 py-4 border-b border-[#202B3F] flex items-center justify-between bg-[#151C2B]">
          <div className="flex items-center gap-2.5">
            <div className={`p-1.5 rounded-lg ${
              severity === 'danger'
                ? 'bg-[#ED4245]/20 text-[#ED4245]'
                : severity === 'warning'
                ? 'bg-[#FEE75C]/20 text-[#FEE75C]'
                : 'bg-[#65D8FF]/20 text-[#65D8FF]'
            }`}>
              <AlertTriangle className="w-4 h-4" />
            </div>
            <h3 className="text-sm font-bold text-white font-mono">{title}</h3>
          </div>

          <button onClick={onCancel} className="text-[#8292AB] hover:text-white transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-6 space-y-4">
          <p className="text-xs text-[#8292AB] leading-relaxed font-sans">
            {description}
          </p>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-[#202B3F]">
            <button
              onClick={onCancel}
              className="px-4 py-2 text-xs font-semibold text-[#8292AB] hover:text-white transition-colors font-mono"
            >
              {cancelLabel}
            </button>
            <button
              onClick={() => {
                onConfirm()
                onCancel()
              }}
              className={`px-4 py-2 text-xs font-bold rounded-lg transition-colors font-mono ${
                severity === 'danger'
                  ? 'bg-[#ED4245] hover:bg-[#d63b3e] text-white'
                  : severity === 'warning'
                  ? 'bg-[#FEE75C] hover:bg-[#ebd553] text-[#090D18]'
                  : 'bg-[#65D8FF] hover:bg-[#52c8ef] text-[#090D18]'
              }`}
            >
              {confirmLabel}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ConfirmationModal
