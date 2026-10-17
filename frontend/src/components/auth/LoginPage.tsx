import React, { useState } from 'react'
import { ShieldCheck, Terminal, ArrowRight, Lock, Mail, AlertCircle, Eye, EyeOff } from 'lucide-react'
import { YuktiLogo } from '../ui/YuktiLogo'
import ParticleBackground from '../ui/particle-background'
import type { User, UserRole } from '../../types/auth'
import ForgotPasswordModal from './ForgotPasswordModal'

interface LoginPageProps {
  onLogin: (user: User) => void
  onNavigateToSignup: () => void
  onNavigateToLanding: () => void
}

export const LoginPage: React.FC<LoginPageProps> = ({
  onLogin,
  onNavigateToSignup,
  onNavigateToLanding,
}) => {
  const [selectedRole, setSelectedRole] = useState<UserRole>('ADMIN')
  const [email, setEmail] = useState('lead@yuktiops.dev')
  const [password, setPassword] = useState('••••••••')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isForgotPasswordOpen, setIsForgotPasswordOpen] = useState(false)

  // Quick switch role preset
  const handleRoleToggle = (role: UserRole) => {
    setSelectedRole(role)
    if (role === 'ADMIN') {
      setEmail('lead@yuktiops.dev')
    } else {
      setEmail('dev@yuktiops.dev')
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError(null)

    setTimeout(() => {
      setIsLoading(false)
      const userHandle = email 
        ? email.split('@')[0].toLowerCase().replace(/[^a-z0-9_]/g, '_') 
        : (selectedRole === 'ADMIN' ? 'lead_eng' : 'dev_eng')
      const formattedName = userHandle
        .split('_')
        .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
        .join(' ') || (selectedRole === 'ADMIN' ? 'Lead Engineer' : 'Software Engineer')

      onLogin({
        id: `usr-${userHandle}`,
        name: formattedName,
        handle: userHandle,
        email: email || (selectedRole === 'ADMIN' ? 'lead@yuktiops.dev' : 'dev@yuktiops.dev'),
        role: selectedRole,
        title: selectedRole === 'ADMIN' ? 'Project Lead' : 'Software Engineer',
        avatar: selectedRole === 'ADMIN'
          ? 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=120&auto=format&fit=crop&q=80'
          : 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=120&auto=format&fit=crop&q=80',
        isOnline: true,
      })
    }, 400)
  }

  return (
    <div className="relative min-h-screen bg-[#090D16] flex flex-col items-center justify-center p-6 selection:bg-[#62CBE8] selection:text-[#07131C] overflow-hidden">
      {/* Restrained background layer */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <ParticleBackground intensity="restrained" className="opacity-25" />
      </div>

      {/* Brand Header */}
      <div className="relative z-10 mb-8">
        <YuktiLogo
          size={22}
          wordmarkSize="2xl"
          badgeText="CORE V1.0"
          markContainerClassName="w-10 h-10 bg-[#111925] border border-[#263246] rounded-xl shadow-sm text-[#62CBE8]"
          badgeClassName="text-xs px-2 py-0.5"
          onClick={onNavigateToLanding}
          className="hover:opacity-90 transition-opacity cursor-pointer"
        />
      </div>

      {/* Main Auth Card */}
      <div className="relative z-10 w-full max-w-md bg-[#111925] border border-[#263246] rounded-2xl p-8 shadow-xl">
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold text-[#F1F5F9] tracking-tight font-sans">Welcome Back</h1>
          <p className="text-sm text-[#A0AEC0] mt-1 font-sans">
            Choose your workspace role to test role-based access
          </p>
        </div>

        {/* Role Switcher Tabs */}
        <div className="grid grid-cols-2 gap-2 bg-[#090D16] p-1.5 rounded-xl border border-[#263246] mb-6">
          <button
            type="button"
            onClick={() => handleRoleToggle('ADMIN')}
            className={`flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-semibold transition-all font-sans ${
              selectedRole === 'ADMIN'
                ? 'bg-[#62CBE8] text-[#07131C] shadow-sm'
                : 'text-[#A0AEC0] hover:text-[#F1F5F9] hover:bg-[#161F2D]'
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Admin / Lead</span>
          </button>

          <button
            type="button"
            onClick={() => handleRoleToggle('DEVELOPER')}
            className={`flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-semibold transition-all font-sans ${
              selectedRole === 'DEVELOPER'
                ? 'bg-[#38B982] text-[#07131C] shadow-sm'
                : 'text-[#A0AEC0] hover:text-[#F1F5F9] hover:bg-[#161F2D]'
            }`}
          >
            <Terminal className="w-3.5 h-3.5" />
            <span>Developer</span>
          </button>
        </div>

        {/* Role Explanation Note */}
        <div className="mb-6 p-3 rounded-xl bg-[#161F2D] border border-[#263246] text-xs font-sans">
          {selectedRole === 'ADMIN' ? (
            <div className="text-[#A0AEC0]">
              <span className="font-semibold text-[#62CBE8]">Admin Mode:</span> Unlocks the AI &amp; Admin Decision Queue, one-click blocker resolution, and team workload radar.
            </div>
          ) : (
            <div className="text-[#A0AEC0]">
              <span className="text-[#A0AEC0]">
                <span className="font-semibold text-[#38B982]">Developer Mode:</span> Access to Team Chat, Task Board, and Git feeds. Admin Inbox route is strictly gated with 403 screen.
              </span>
            </div>
          )}
        </div>

        {/* GitHub Quick Login */}
        <button
          type="button"
          onClick={() => handleSubmit({ preventDefault: () => {} } as React.FormEvent)}
          className="w-full py-2.5 px-4 bg-[#161F2D] hover:bg-[#1E293B] text-[#F1F5F9] border border-[#263246] rounded-xl text-sm font-semibold flex items-center justify-center gap-3 transition-colors mb-4 font-sans"
        >
          <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24">
            <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
          </svg>
          <span>Continue with GitHub</span>
        </button>

        <div className="flex items-center my-4">
          <div className="flex-1 border-t border-[#263246]"></div>
          <span className="px-3 text-xs font-mono text-[#77869B]">OR EMAIL</span>
          <div className="flex-1 border-t border-[#263246]"></div>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-[#E47777]/10 border border-[#E47777]/30 rounded-lg flex items-center gap-2 text-xs text-[#E47777]">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Credentials Form */}
        <form onSubmit={handleSubmit} className="space-y-4 font-sans">
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
                className="w-full bg-[#161F2D] border border-[#263246] focus:border-[#62CBE8] focus:ring-1 focus:ring-[#62CBE8] rounded-xl px-3.5 py-2.5 text-sm text-[#F1F5F9] placeholder-[#77869B] outline-none pl-10 transition-colors font-sans"
                placeholder="developer@team.com"
              />
              <Mail className="w-4 h-4 text-[#77869B] absolute left-3.5 top-3" />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5 font-mono">
              <label className="text-xs font-semibold text-[#A0AEC0] uppercase tracking-wider">
                Password
              </label>
              <button
                type="button"
                onClick={() => setIsForgotPasswordOpen(true)}
                className="text-[11px] text-[#62CBE8] hover:underline"
              >
                Forgot Password?
              </button>
            </div>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full bg-[#161F2D] border border-[#263246] focus:border-[#62CBE8] focus:ring-1 focus:ring-[#62CBE8] rounded-xl px-3.5 py-2.5 text-sm text-[#F1F5F9] placeholder-[#77869B] outline-none pl-10 pr-10 transition-colors font-sans"
                placeholder="••••••••"
              />
              <Lock className="w-4 h-4 text-[#77869B] absolute left-3.5 top-3" />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3.5 top-2.5 text-[#77869B] hover:text-[#F1F5F9] transition-colors p-0.5 rounded"
                title={showPassword ? 'Hide password' : 'Show password'}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3 bg-[#62CBE8] hover:bg-[#79D6EE] disabled:opacity-50 text-[#07131C] font-semibold rounded-xl text-sm shadow-md flex items-center justify-center gap-2 transition-all mt-6 font-mono"
          >
            {isLoading ? (
              <span className="inline-block w-4 h-4 border-2 border-[#07131C] border-t-transparent rounded-full animate-spin"></span>
            ) : (
              <>
                <span>Enter Workspace as {selectedRole === 'ADMIN' ? 'Admin' : 'Developer'}</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        {/* Footer info */}
        <div className="mt-6 pt-5 border-t border-[#263246] text-center text-xs text-[#A0AEC0] font-sans">
          Don&apos;t have an account?{' '}
          <button
            type="button"
            onClick={onNavigateToSignup}
            className="text-[#62CBE8] hover:underline font-semibold ml-1 font-mono"
          >
            Sign up
          </button>
        </div>
      </div>

      <ForgotPasswordModal
        isOpen={isForgotPasswordOpen}
        onClose={() => setIsForgotPasswordOpen(false)}
      />
    </div>
  )
}

export default LoginPage
