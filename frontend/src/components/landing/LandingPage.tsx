import React, { useState, useEffect } from 'react'
import { motion, useScroll, useSpring } from 'framer-motion'
import { 
  ArrowRight, 
  Terminal, 
  GitPullRequest, 
  CheckCircle2, 
  MessageSquare, 
  Layers, 
  Activity, 
  UserCheck, 
  ChevronRight,
  ShieldCheck,
  FileCheck
} from 'lucide-react'
import ParticleBackground from '../ui/particle-background'
import CinematicHero from './CinematicHero'
import KineticTypography from './KineticTypography'
import PinnedWorkflow from './PinnedWorkflow'
import ScreensShowcase from './ScreensShowcase'
import { YuktiMark, YuktiLogo, YuktiWordmark } from '../ui/YuktiLogo'

interface LandingPageProps {
  onEnterApp: () => void
  onGoToLogin: () => void
  onGoToSignup: () => void
}

export const LandingPage: React.FC<LandingPageProps> = ({
  onEnterApp,
  onGoToLogin,
  onGoToSignup,
}) => {
  const [isScrolled, setIsScrolled] = useState(false)
  const [activeSection, setActiveSection] = useState('overview')

  const { scrollYProgress } = useScroll()
  const scaleX = useSpring(scrollYProgress, {
    stiffness: 100,
    damping: 30,
    restDelta: 0.001,
  })

  useEffect(() => {
    const handleScroll = () => {
      const scrollY = window.scrollY
      setIsScrolled(scrollY > 50)

      const sections = ['overview', 'workflow', 'narrative', 'capabilities', 'workspace', 'governance']
      for (const sectionId of sections) {
        const el = document.getElementById(sectionId)
        if (el) {
          const rect = el.getBoundingClientRect()
          if (rect.top <= 200 && rect.bottom >= 200) {
            setActiveSection(sectionId)
            break
          }
        }
      }
    }

    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <div className="relative min-h-screen bg-[#090D16] text-[#F1F5F9] overflow-x-clip selection:bg-[#62CBE8] selection:text-[#07131C] font-sans">
      {/* 0. SHARED FULL-PAGE PERSISTENT ANIMATED BACKGROUND */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <ParticleBackground intensity="story" />
      </div>

      {/* 1. TOP SCROLL PROGRESS INDICATOR */}
      <motion.div
        className="fixed top-0 left-0 right-0 h-[2px] bg-[#62CBE8] origin-left z-50 pointer-events-none"
        style={{ scaleX }}
      />

      {/* 2. ADAPTIVE NAVIGATION (Geist Sans, transparent -> frosted midnight) */}
      <nav
        className={`fixed top-0 left-0 right-0 z-40 transition-all duration-300 ${
          isScrolled
            ? 'bg-[#090D16]/90 backdrop-blur-md border-b border-[#263246] py-3.5 shadow-xl'
            : 'bg-transparent py-5'
        }`}
      >
        <div className="max-w-7xl mx-auto px-6 flex items-center justify-between">
          {/* Brand Logo with Connected Intelligence Mark */}
          <YuktiLogo
            size={20}
            wordmarkSize="lg"
            badgeText="CORE V1.0"
            className="group cursor-pointer"
            markContainerClassName="w-8 h-8 rounded-lg bg-[#111925] border border-[#263246] group-hover:border-[#62CBE8]/60 transition-colors"
            badgeClassName="bg-[#161F2D] border-[#263246]"
            onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          />

          {/* Nav Links in Geist Sans */}
          <div className="hidden lg:flex items-center gap-7 text-xs font-medium text-[#A0AEC0]">
            {[
              { id: 'overview', label: 'Platform Overview' },
              { id: 'workflow', label: 'Workflow Automation' },
              { id: 'capabilities', label: 'Core Capabilities' },
              { id: 'workspace', label: 'Workspace' },
              { id: 'governance', label: 'Access & Governance' },
            ].map((link) => (
              <a
                key={link.id}
                href={`#${link.id}`}
                className={`transition-colors hover:text-white ${
                  activeSection === link.id ? 'text-[#62CBE8] font-semibold' : ''
                }`}
              >
                {link.label}
              </a>
            ))}
          </div>

          {/* Action CTAs in Geist Sans */}
          <div className="flex items-center gap-3 text-xs font-medium">
            <button
              onClick={onGoToLogin}
              className="px-3.5 py-2 text-[#F1F5F9] hover:text-white hover:bg-[#161F2D] rounded-lg transition-colors font-sans"
            >
              Sign In
            </button>
            <button
              onClick={onGoToSignup}
              className="hidden sm:inline-block px-3.5 py-2 text-[#A0AEC0] hover:text-white hover:bg-[#161F2D] rounded-lg border border-[#263246] transition-colors font-sans"
            >
              Register
            </button>
            <button
              onClick={onEnterApp}
              className="px-4 py-2 bg-[#62CBE8] hover:bg-[#79D6EE] text-[#07131C] font-semibold rounded-lg flex items-center gap-2 transition-colors font-sans"
            >
              <span>Open Workspace</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </nav>

      {/* 3. COORDINATED CINEMATIC HERO (Continuous Storytelling Sequence) */}
      <section id="overview" className="relative z-10">
        <CinematicHero 
          onEnterApp={onEnterApp}
          onGoToLogin={onGoToLogin}
          onGoToSignup={onGoToSignup}
        />
      </section>

      {/* 4. KINETIC TYPOGRAPHY PILLARS SECTION */}
      <section id="narrative" className="relative z-10 py-16 px-6 bg-[#090D16] border-t border-[#263246]">
        <div className="max-w-6xl mx-auto">
          <KineticTypography />
        </div>
      </section>

      {/* 5. THE SIGNATURE PINNED WORKFLOW THEATRE */}
      <div className="relative z-10">
        <PinnedWorkflow />
      </div>

      {/* 6. CORE CAPABILITIES (Editorial Split Surface) */}
      <section id="capabilities" className="relative z-10 py-24 px-6 bg-[#090D16] border-b border-[#263246]">
        <div className="max-w-6xl mx-auto space-y-16">
          <div className="text-center space-y-3">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#111925] border border-[#263246] text-xs font-sans font-medium text-[#62CBE8]">
              <span>CORE CAPABILITIES</span>
            </div>
            <h2 className="font-display text-xl sm:text-3xl text-white tracking-wide font-normal">
              Core Capabilities
            </h2>
            <p className="text-sm sm:text-base text-[#A0AEC0] max-w-2xl mx-auto font-sans font-normal">
              Connect conversation evidence, task coordination, repository events, and lead approvals into one operating model.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            {/* Left Column: Architectural Thesis & Operating Principles */}
            <div className="lg:col-span-5 space-y-6">
              <div className="space-y-3">
                <h3 className="font-display text-lg sm:text-xl text-white tracking-wide font-normal">
                  Four pillars of connected engineering operations.
                </h3>
                <p className="text-sm text-[#A0AEC0] leading-relaxed font-sans">
                  YuktiOps bridges informal discussions, task boards, and repository events into one operating model—replacing guesswork and siloed status checks with continuous, verifiable context.
                </p>
              </div>

              {/* Operating Principles Box */}
              <div className="p-5 rounded-xl bg-[#111925] border border-[#263246] space-y-4">
                <span className="text-[11px] font-mono text-[#77869B] uppercase tracking-wider block">
                  Operating Principles
                </span>

                <div className="space-y-3 text-xs">
                  <div className="flex items-start gap-2.5">
                    <FileCheck className="w-4 h-4 text-[#62CBE8] shrink-0 mt-0.5" />
                    <div>
                      <span className="font-semibold text-white block">Evidence Grounding</span>
                      <span className="text-[#A0AEC0]">Original conversation quotes and Git commits preserved without alteration.</span>
                    </div>
                  </div>

                  <div className="flex items-start gap-2.5">
                    <ShieldCheck className="w-4 h-4 text-[#62CBE8] shrink-0 mt-0.5" />
                    <div>
                      <span className="font-semibold text-white block">Human Governance</span>
                      <span className="text-[#A0AEC0]">Consequential actions require explicit technical lead authorization.</span>
                    </div>
                  </div>

                  <div className="flex items-start gap-2.5">
                    <Activity className="w-4 h-4 text-[#62CBE8] shrink-0 mt-0.5" />
                    <div>
                      <span className="font-semibold text-white block">Complete Traceability</span>
                      <span className="text-[#A0AEC0]">Every approved task update and blocker logged in the permanent audit ledger.</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column: Unified Capability Surface */}
            <div className="lg:col-span-7 bg-[#111925] border border-[#263246] rounded-2xl divide-y divide-[#263246] overflow-hidden">
              {/* Capability 1 */}
              <div className="p-6 sm:p-7 space-y-3">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-[#161F2D] border border-[#263246] flex items-center justify-center text-[#62CBE8]">
                    <MessageSquare className="w-4 h-4" />
                  </div>
                  <h4 className="text-base font-semibold text-white font-sans">
                    Conversation Intelligence
                  </h4>
                </div>
                <p className="text-sm text-[#A0AEC0] leading-relaxed font-sans">
                  Understand relevant team messages, including supported English and Hinglish input, to identify potential blockers, dependencies, and action items.
                </p>
                <div className="text-xs font-sans text-[#62CBE8]">
                  Implementation: Natural language parser normalizes conversation signals into structured task updates with original quotes preserved.
                </div>
              </div>

              {/* Capability 2 */}
              <div className="p-6 sm:p-7 space-y-3">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-[#161F2D] border border-[#263246] flex items-center justify-center text-[#62CBE8]">
                    <Layers className="w-4 h-4" />
                  </div>
                  <h4 className="text-base font-semibold text-white font-sans">
                    Cross-Tool Context
                  </h4>
                </div>
                <p className="text-sm text-[#A0AEC0] leading-relaxed font-sans">
                  Connect conversation evidence with task records, repository events, pull requests, commits, and project history into a unified operating context.
                </p>
                <div className="text-xs font-sans text-[#62CBE8]">
                  Implementation: Bidirectional links connect chat threads, task IDs, and GitHub repository activity.
                </div>
              </div>

              {/* Capability 3 */}
              <div className="p-6 sm:p-7 space-y-3">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-[#161F2D] border border-[#263246] flex items-center justify-center text-[#62CBE8]">
                    <GitPullRequest className="w-4 h-4" />
                  </div>
                  <h4 className="text-base font-semibold text-white font-sans">
                    Blocker Detection &amp; Resolution
                  </h4>
                </div>
                <p className="text-sm text-[#A0AEC0] leading-relaxed font-sans">
                  Surface potential blockers across ongoing work, explain relevance using available evidence, and recommend concrete next steps.
                </p>
                <div className="text-xs font-sans text-[#62CBE8]">
                  Implementation: Synthesizes dependency risks and generates targeted mitigation recommendations.
                </div>
              </div>

              {/* Capability 4 */}
              <div className="p-6 sm:p-7 space-y-3">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-[#161F2D] border border-[#263246] flex items-center justify-center text-[#62CBE8]">
                    <Activity className="w-4 h-4" />
                  </div>
                  <h4 className="text-base font-semibold text-white font-sans">
                    Human-Governed Actions
                  </h4>
                </div>
                <p className="text-sm text-[#A0AEC0] leading-relaxed font-sans">
                  Route consequential recommendations to authorized technical leads for review, respect role permissions, and maintain a verifiable decision trail.
                </p>
                <div className="text-xs font-sans text-[#62CBE8]">
                  Implementation: One-click lead authorization with audit logging and role-gated execution.
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 7. INTERACTIVE 5-SCREEN SHOWCASE */}
      <div className="relative z-10">
        <ScreensShowcase onLaunchWorkspace={onEnterApp} />
      </div>

      {/* 8. ACCESS CONTROL & GOVERNANCE */}
      <section id="governance" className="relative z-10 py-24 px-6 bg-[#090D16] border-b border-[#263246]">
        <div className="max-w-6xl mx-auto space-y-12">
          <div className="text-center space-y-3">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#111925] border border-[#263246] text-xs font-sans font-medium text-[#62CBE8]">
              <span>ACCESS CONTROL &amp; GOVERNANCE</span>
            </div>
            <h2 className="font-display text-xl sm:text-3xl text-white tracking-wide font-normal">
              Access Control &amp; Governance
            </h2>
            <p className="text-sm sm:text-base text-[#A0AEC0] max-w-xl mx-auto font-sans font-normal">
              Role-based permissions separate execution workflows from administrative governance, ensuring technical leads retain authoritative approval control while developers work without friction.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Admin View Card */}
            <div className="p-7 bg-[#111925] border border-[#263246] hover:border-[#62CBE8]/40 rounded-xl space-y-4 transition-colors">
              <div className="flex items-center justify-between">
                <span className="px-2.5 py-1 bg-[#161F2D] text-[#62CBE8] font-sans text-xs font-semibold rounded border border-[#263246]">
                  ROLE: ADMINISTRATOR / LEAD
                </span>
                <UserCheck className="w-5 h-5 text-[#62CBE8]" />
              </div>
              <h3 className="text-xl font-bold text-white font-sans">Admin Decision Suite</h3>
              <ul className="space-y-3 text-sm text-[#A0AEC0] font-sans font-normal">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-[#38B982] shrink-0 mt-0.5" />
                  <span>Access to the <strong>AI &amp; Decision Inbox</strong> to review, approve, or reject blocker proposals with evidence-backed clarity.</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-[#38B982] shrink-0 mt-0.5" />
                  <span>Full Command Center visibility into team workload distribution, delivery bottlenecks, and project progress.</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-[#38B982] shrink-0 mt-0.5" />
                  <span>Authoritative control over task state transitions, priority overrides, and decision audit logs.</span>
                </li>
              </ul>
            </div>

            {/* Developer View Card */}
            <div className="p-7 bg-[#111925] border border-[#263246] rounded-xl space-y-4">
              <div className="flex items-center justify-between">
                <span className="px-2.5 py-1 bg-[#161F2D] text-[#A0AEC0] font-sans text-xs font-semibold rounded border border-[#263246]">
                  ROLE: DEVELOPER / MEMBER
                </span>
                <Terminal className="w-5 h-5 text-[#38B982]" />
              </div>
              <h3 className="text-xl font-bold text-white font-sans">Developer Execution View</h3>
              <ul className="space-y-3 text-sm text-[#A0AEC0] font-sans font-normal">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-[#38B982] shrink-0 mt-0.5" />
                  <span>Focused access to Team Conversations, Task Board, and connected GitHub repository streams.</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-[#38B982] shrink-0 mt-0.5" />
                  <span>Ability to flag blockers from conversations and propose status updates with contextual evidence.</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-[#38B982] shrink-0 mt-0.5" />
                  <span>Admin Decision Inbox is access-restricted: unauthorized routes are gated with explicit permission verification.</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* 9. FINAL CALL TO ACTION */}
      <section className="relative z-10 py-20 px-6 text-center bg-[#111925] border-t border-b border-[#263246]">
        <div className="max-w-4xl mx-auto space-y-6 relative z-10">
          <h2 className="font-display text-xl sm:text-3xl text-white tracking-wide font-normal leading-snug">
            Bring Structure and Traceability to Engineering Operations
          </h2>
          <p className="text-[#A0AEC0] text-base sm:text-lg max-w-2xl mx-auto font-sans font-normal">
            Evaluate the YuktiOps platform. Connect team communication, task coordination, and repository activity into one evidence-backed workspace.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-4 text-xs font-semibold pt-2">
            <button
              onClick={onEnterApp}
              className="px-6 py-3 bg-[#62CBE8] hover:bg-[#79D6EE] text-[#07131C] font-semibold rounded-lg flex items-center gap-2 transition-colors font-sans"
            >
              <span>Open Workspace</span>
              <ChevronRight className="w-4 h-4" />
            </button>
            <button
              onClick={onGoToLogin}
              className="px-6 py-3 bg-[#161F2D] hover:bg-[#111925] text-[#F1F5F9] border border-[#263246] font-medium rounded-lg transition-colors font-sans"
            >
              Sign In with Role
            </button>
          </div>
        </div>
      </section>

      {/* 10. TECHNICAL FOOTER */}
      <footer className="relative z-10 py-8 px-6 border-t border-[#263246] bg-[#090D16] text-xs text-[#77869B] max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 font-mono">
        <div className="flex items-center gap-2">
          <YuktiMark size={16} />
          <YuktiWordmark size="sm" />
          <span className="text-[#77869B] ml-2">© 2026. Built by TechSena.</span>
        </div>
        <div className="flex items-center gap-6 text-[11px]">
          <span>Michroma Display</span>
          <span>Geist Sans UI</span>
          <span>Geist Mono Code</span>
          <span>Tailwind v4</span>
        </div>
      </footer>
    </div>
  )
}

export default LandingPage
