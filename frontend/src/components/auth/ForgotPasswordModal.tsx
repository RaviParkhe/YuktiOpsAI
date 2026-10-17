import React, { useState } from 'react'
import { X, Mail, CheckCircle2, ArrowRight } from 'lucide-react'

interface ForgotPasswordModalProps {
  isOpen: boolean
  onClose: () => void
}

export const ForgotPasswordModal: React.FC<ForgotPasswordModalProps> = ({
  isOpen,
  onClose,
}) => {
  const [email, setEmail] = useState('')
  const [isSubmitted, setIsSubmitted] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  if (!isOpen) return null

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!email.trim()) return

    setIsLoading(true)
    setTimeout(() => {
      setIsLoading(false)
      setIsSubmitted(true)
    }, 500)
  }

  const handleReset = () => {
    setEmail('')
    setIsSubmitted(false)
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#090D16]/80 backdrop-blur-sm p-4">
      <div className="w-full max-w-md bg-[#111925] border border-[#263246] rounded-2xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        <div className="px-6 py-4 border-b border-[#263246] flex items-center justify-between bg-[#161F2D]">
          <h3 className="text-sm font-bold text-[#F1F5F9] font-mono">Reset Workspace Password</h3>
          <button onClick={handleReset} className="text-[#A0AEC0] hover:text-[#F1F5F9] transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6">
          {isSubmitted ? (
            <div className="text-center py-4 space-y-4">
              <div className="w-12 h-12 rounded-full bg-[#38B982]/20 border border-[#38B982]/40 flex items-center justify-center text-[#38B982] mx-auto">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <h4 className="text-base font-bold text-[#F1F5F9] font-sans">
                Recovery Dispatch Sent
              </h4>
              <p className="text-xs text-[#A0AEC0] leading-relaxed font-sans max-w-xs mx-auto">
                If an account with <strong className="text-[#F1F5F9] font-mono">{email}</strong> exists, instructions to securely reset your credentials have been sent.
              </p>
              <button
                onClick={handleReset}
                className="w-full py-2.5 bg-[#161F2D] hover:bg-[#1E293B] text-[#F1F5F9] border border-[#263246] text-xs font-semibold rounded-xl transition-colors font-mono"
              >
                Return to Sign In
              </button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4 font-sans">
              <p className="text-xs text-[#A0AEC0] leading-relaxed font-sans">
                Enter your verified developer or administrator email address to receive password recovery instructions.
              </p>

              <div>
                <label className="block text-xs font-semibold text-[#A0AEC0] uppercase tracking-wider mb-1.5 font-mono">
                  Email Address
                </label>
                <div className="relative">
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    placeholder="developer@team.com"
                    className="w-full bg-[#161F2D] border border-[#263246] focus:border-[#62CBE8] focus:ring-1 focus:ring-[#62CBE8] rounded-xl px-3.5 py-2.5 text-sm text-[#F1F5F9] placeholder-[#77869B] outline-none pl-10 transition-colors font-sans"
                  />
                  <Mail className="w-4 h-4 text-[#77869B] absolute left-3.5 top-3" />
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-[#263246]">
                <button
                  type="button"
                  onClick={handleReset}
                  className="px-4 py-2 text-xs font-semibold text-[#A0AEC0] hover:text-[#F1F5F9] transition-colors font-mono"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isLoading || !email.trim()}
                  className="px-5 py-2.5 bg-[#62CBE8] hover:bg-[#79D6EE] disabled:opacity-50 text-[#07131C] font-bold text-xs rounded-xl flex items-center gap-2 transition-all font-mono"
                >
                  {isLoading ? (
                    <span className="w-4 h-4 border-2 border-[#07131C] border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <>
                      <span>Send Link</span>
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}

export default ForgotPasswordModal
