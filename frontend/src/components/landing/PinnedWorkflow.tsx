import React, { useState } from 'react'
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion'
import { 
  Kanban, 
  GitPullRequest, 
  ShieldCheck, 
  Check, 
  ChevronRight, 
  CheckCircle2 
} from 'lucide-react'
import { YuktiMark } from '../ui/YuktiLogo'

interface WorkflowStep {
  id: number
  badge: string
  title: string
  tabLabel: string
  subtitle: string
  accentColor: string
  borderColor: string
  renderVisual: (isApproved: boolean, onApprove: () => void) => React.ReactNode
}

export const PinnedWorkflow: React.FC = () => {
  const [currentStep, setCurrentStep] = useState(0)
  const [isDemoApproved, setIsDemoApproved] = useState(false)
  const shouldReduceMotion = useReducedMotion()

  const STEPS: WorkflowStep[] = [
    {
      id: 1,
      badge: '01 // SIGNAL DETECTION',
      title: 'Signal Detection in Team Conversations',
      tabLabel: 'Signal Detection',
      subtitle: 'Identify potential blockers, dependencies, and requests in team conversations across supported English and Hinglish messages.',
      accentColor: 'text-[#62CBE8]',
      borderColor: 'border-[#62CBE8]',
      renderVisual: () => (
        <div className="bg-[#111925] border border-[#263246] rounded-xl p-5 shadow-xl">
          <div className="flex items-center justify-between text-xs text-[#A0AEC0] mb-3 font-mono">
            <span>#frontend · Team Discussion Channel</span>
            <span>10:42 AM</span>
          </div>
          <div className="flex items-start gap-3">
            <img
              src="https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=120&auto=format&fit=crop&q=80"
              alt="Priya"
              className="w-10 h-10 rounded-full border border-[#62CBE8]/40 object-cover"
            />
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className="font-bold text-[#F1F5F9] text-sm">Priya Sharma</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#090D16] text-[#62CBE8] border border-[#62CBE8]/30">
                  Frontend Dev
                </span>
              </div>
              <div className="mt-2 p-3 bg-[#090D16] rounded-lg border border-[#263246] text-sm text-[#F1F5F9] font-mono leading-relaxed">
                &quot;Login UI page done, but backend auth API nahi mila yet.&quot;
              </div>
              <span className="text-[11px] font-mono text-[#77869B] mt-2 block">
                Source language: Hinglish · Original conversation quote preserved as verifiable evidence.
              </span>
            </div>
          </div>
        </div>
      ),
    },
    {
      id: 2,
      badge: '02 // CONTEXT CORRELATION',
      title: 'Context Correlation with Project State',
      tabLabel: 'Context Correlation',
      subtitle: 'Associate the detected signal with relevant tasks, pull requests, commits, and project context.',
      accentColor: 'text-[#E5B85C]',
      borderColor: 'border-[#E5B85C]',
      renderVisual: () => (
        <div className="bg-[#111925] border border-[#263246] rounded-xl p-5 shadow-xl space-y-4">
          <div className="flex items-center justify-between text-xs font-mono">
            <span className="text-[#E5B85C] font-bold flex items-center gap-2">
              <YuktiMark size={14} className="text-[#62CBE8]" />
              YUKTI CORE · CONTEXT ENGINE
            </span>
            <span className="px-2 py-0.5 rounded bg-[#E5B85C]/10 text-[#E5B85C] border border-[#E5B85C]/30">
              Confidence: 94%
            </span>
          </div>

          <div className="p-3.5 bg-[#090D16] rounded-lg border border-[#263246] space-y-2 text-xs font-mono">
            <div className="flex justify-between">
              <span className="text-[#A0AEC0]">Target Issue:</span>
              <span className="text-[#F1F5F9] font-bold">Dependency Blocker (P0)</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#A0AEC0]">Waiting On:</span>
              <span className="text-[#E5B85C]">Backend Auth Endpoints &amp; Token Specs</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#A0AEC0]">Affected Task:</span>
              <span className="text-[#62CBE8]">YUKTI-104</span>
            </div>
          </div>

          <div className="text-[11px] text-[#A0AEC0] font-mono flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-[#E5B85C]" />
            <span>Correlated with project dependencies without notification noise.</span>
          </div>
        </div>
      ),
    },
    {
      id: 3,
      badge: '03 // BLOCKER ASSESSMENT',
      title: 'Blocker Assessment & Evidence Mapping',
      tabLabel: 'Blocker Assessment',
      subtitle: 'Evaluate the issue against repository status and active pull requests to verify impact.',
      accentColor: 'text-[#62CBE8]',
      borderColor: 'border-[#62CBE8]',
      renderVisual: () => (
        <div className="bg-[#111925] border border-[#263246] rounded-xl p-5 shadow-xl space-y-3">
          <div className="text-xs font-mono text-[#A0AEC0] flex items-center justify-between">
            <span className="font-bold text-[#F1F5F9] flex items-center gap-1.5">
              <Kanban className="w-4 h-4 text-[#62CBE8]" />
              TASK RECORD: YUKTI-104
            </span>
            <span className="text-[#E5B85C] font-mono">Status: In Progress → Blocked</span>
          </div>

          <div className="p-3 bg-[#090D16] rounded-lg border border-[#263246] text-xs space-y-2">
            <div className="font-bold text-[#F1F5F9]">Client-side Auth &amp; API Integration</div>
            <div className="text-[#A0AEC0] font-mono text-[11px]">
              Assignee: Priya Sharma · Priority: P0 Critical
            </div>
          </div>

          {/* GitHub PR Correlation */}
          <div className="p-3 bg-[#090D16] rounded-lg border border-[#263246] flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <GitPullRequest className="w-4 h-4 text-[#38B982]" />
              <div>
                <span className="font-bold text-[#F1F5F9]">PR #14: feat: login-flow</span>
                <span className="text-[#77869B] font-mono text-[10px] block">Branch: feat/login-flow → main</span>
              </div>
            </div>
            <span className="px-2 py-0.5 rounded bg-[#38B982]/10 text-[#38B982] border border-[#38B982]/30 font-mono text-[10px] font-bold">
              OPEN
            </span>
          </div>
        </div>
      ),
    },
    {
      id: 4,
      badge: '04 // ACTION RECOMMENDATION',
      title: 'Structured Action Recommendation',
      tabLabel: 'Action Recommendation',
      subtitle: 'Propose concrete task state updates and assignment adjustments with clear supporting rationale.',
      accentColor: 'text-[#E5B85C]',
      borderColor: 'border-[#E5B85C]',
      renderVisual: () => (
        <div className="bg-[#111925] border border-[#263246] rounded-xl p-5 shadow-xl space-y-3">
          <div className="flex items-center justify-between text-xs font-mono">
            <span className="text-[#E5B85C] font-bold flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4" />
              LEAD REVIEW REQUIRED
            </span>
            <span className="px-2 py-0.5 bg-[#E5B85C]/10 text-[#E5B85C] border border-[#E5B85C]/30 rounded font-bold">
              Evidence-Backed Proposal
            </span>
          </div>

          <div className="p-3 bg-[#090D16] rounded-lg border border-[#263246] text-xs space-y-1.5">
            <div className="text-[#A0AEC0] font-mono">Recommendation:</div>
            <div className="text-[#F1F5F9] font-semibold">
              Mark YUKTI-104 as Blocked &amp; assign follow-up to Backend Engineer (@alex_chen).
            </div>
          </div>

          <div className="bg-[#090D16] p-2.5 rounded border border-[#263246] text-[11px] font-mono text-[#62CBE8]">
            Evidence: &quot;Login UI page done, but backend auth API nahi mila yet.&quot;
          </div>
        </div>
      ),
    },
    {
      id: 5,
      badge: '05 // HUMAN REVIEW & APPROVAL',
      title: 'Human Review & Traceable Execution',
      tabLabel: 'Review & Approval',
      subtitle: 'Route consequential actions to an authorized lead for review and record the decision in the permanent audit trail.',
      accentColor: 'text-[#38B982]',
      borderColor: 'border-[#38B982]',
      renderVisual: (isApproved, onApprove) => (
        <div className="bg-[#111925] border border-[#263246] rounded-xl p-5 shadow-xl space-y-4">
          <div className="flex items-center justify-between text-xs font-mono">
            <span className="text-[#38B982] font-bold flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4" />
              STATUS SYNCHRONIZATION
            </span>
            <span className="text-[#77869B] font-mono">Audit Logged</span>
          </div>

          <div className="p-4 bg-[#090D16] rounded-lg border border-[#263246] text-xs space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[#A0AEC0] font-mono">YUKTI-104 Status:</span>
              <span className={`font-mono font-bold px-2 py-0.5 rounded border ${isApproved ? 'bg-[#E47777]/10 text-[#E47777] border-[#E47777]/30' : 'bg-[#161F2D] text-[#A0AEC0] border-[#263246]'}`}>
                {isApproved ? 'BLOCKED (VERIFIED)' : 'AWAITING APPROVAL'}
              </span>
            </div>
            <div className="text-[11px] text-[#77869B] font-mono">
              Audit Record: Approved by Aarav Mehta (Project Lead) · Synced to Task Board
            </div>
          </div>

          <div className="pt-2">
            <button
              onClick={onApprove}
              className={`w-full py-2.5 rounded-lg text-xs font-semibold font-sans flex items-center justify-center gap-2 transition-all ${
                isApproved
                  ? 'bg-[#38B982] text-[#07131C] shadow-md'
                  : 'bg-[#161F2D] hover:bg-[#1E293B] text-[#F1F5F9] border border-[#263246]'
              }`}
            >
              <Check className="w-4 h-4" />
              <span>{isApproved ? '✓ APPROVED & SYNCHRONIZED TO BOARD' : 'Click to Approve Recommendation'}</span>
            </button>
          </div>
        </div>
      ),
    },
  ]

  const activeStepData = STEPS[currentStep]

  return (
    <section id="workflow" className="py-24 px-6 bg-[#090D16] border-t border-b border-[#263246] relative overflow-hidden">
      {/* Decorative Technical Grid */}
      <div className="absolute inset-0 tech-grid opacity-15 pointer-events-none" />

      <div className="max-w-6xl mx-auto relative z-10">
        {/* Section Header */}
        <div className="text-center mb-16 space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded bg-[#111925] border border-[#263246] text-xs font-sans font-medium text-[#62CBE8]">
            <span className="w-1.5 h-1.5 rounded-full bg-[#62CBE8]" />
            <span>WORKFLOW AUTOMATION</span>
          </div>
          <h2 className="font-display text-xl sm:text-3xl text-[#F1F5F9] tracking-wide font-normal">
            From Team Signals to Actionable Decisions
          </h2>
          <p className="text-sm sm:text-base text-[#A0AEC0] max-w-2xl mx-auto font-sans font-normal">
            Connect conversations, task states, and repository activity in a traceable workflow that helps teams identify dependencies and resolve blockers.
          </p>
        </div>

        {/* Step Navigation Tabs */}
        <div className="flex items-center justify-center gap-2 sm:gap-3 mb-12 flex-wrap">
          {STEPS.map((s, idx) => (
            <button
              key={s.id}
              onClick={() => setCurrentStep(idx)}
              className={`px-3.5 py-2 rounded-lg text-xs font-sans font-medium transition-all flex items-center gap-2 border ${
                idx === currentStep
                  ? 'bg-[#111925] text-[#62CBE8] border-[#62CBE8]'
                  : 'bg-[#161F2D] text-[#A0AEC0] border-[#263246] hover:text-[#F1F5F9]'
              }`}
            >
              <span className="font-semibold">{s.id.toString().padStart(2, '0')}</span>
              <span className="hidden md:inline">{s.tabLabel}</span>
            </button>
          ))}
        </div>

        {/* Pinned Workflow Theatre Stage */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center bg-[#111925] border border-[#263246] rounded-2xl p-6 sm:p-10 shadow-xl">
          {/* Left Column: Narrative Context */}
          <div className="lg:col-span-6 space-y-5">
            <span className={`text-xs font-mono font-semibold tracking-wider ${activeStepData.accentColor} block`}>
              {activeStepData.badge}
            </span>

            <h3 className="text-2xl sm:text-3xl font-bold text-[#F1F5F9] tracking-tight leading-tight">
              {activeStepData.title}
            </h3>

            <p className="text-sm sm:text-base text-[#A0AEC0] leading-relaxed font-sans">
              {activeStepData.subtitle}
            </p>

            {/* Stepper Controls */}
            <div className="flex items-center gap-4 pt-4 border-t border-[#263246]">
              <button
                disabled={currentStep === 0}
                onClick={() => setCurrentStep((prev) => Math.max(0, prev - 1))}
                className="px-4 py-2 rounded-lg bg-[#161F2D] hover:bg-[#1E293B] disabled:opacity-40 text-xs font-sans font-medium text-[#F1F5F9] border border-[#263246] transition-colors"
              >
                ← Previous
              </button>

              <button
                disabled={currentStep === STEPS.length - 1}
                onClick={() => setCurrentStep((prev) => Math.min(STEPS.length - 1, prev + 1))}
                className="px-4 py-2 rounded-lg bg-[#62CBE8] hover:bg-[#79D6EE] disabled:opacity-40 text-[#07131C] font-semibold text-xs font-sans transition-colors flex items-center gap-1.5"
              >
                <span>Next Stage</span>
                <ChevronRight className="w-4 h-4" />
              </button>

              <span className="text-xs font-mono text-[#77869B] ml-auto">
                Step {currentStep + 1} of {STEPS.length}
              </span>
            </div>
          </div>

          {/* Right Column: Visual Stage */}
          <div className="lg:col-span-6">
            <AnimatePresence mode="wait">
              <motion.div
                key={activeStepData.id}
                initial={shouldReduceMotion ? { opacity: 1 } : { opacity: 0, scale: 0.96 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={shouldReduceMotion ? { opacity: 1 } : { opacity: 0, scale: 0.96 }}
                transition={{ duration: 0.3, ease: 'easeOut' }}
              >
                {activeStepData.renderVisual(isDemoApproved, () => setIsDemoApproved(!isDemoApproved))}
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </div>
    </section>
  )
}

export default PinnedWorkflow
