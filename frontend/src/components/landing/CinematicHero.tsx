import React, { useState, useEffect, useRef } from 'react'
import { 
  ArrowRight, 
  MessageSquare, 
  Kanban, 
  GitPullRequest, 
  Sparkles,
  ShieldCheck, 
  CheckCircle2, 
  AlertTriangle, 
  ChevronDown 
} from 'lucide-react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import YuktiCoreScene from '../core/YuktiCoreScene'
import { YuktiMark, YuktiWordmark } from '../ui/YuktiLogo'

gsap.registerPlugin(ScrollTrigger)

interface CinematicHeroProps {
  onEnterApp: () => void
  onGoToLogin: () => void
  onGoToSignup: () => void
}

export const CinematicHero: React.FC<CinematicHeroProps> = ({
  onEnterApp,
  onGoToLogin,
  onGoToSignup: _onGoToSignup,
}) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const pinStageRef = useRef<HTMLDivElement>(null)
  const coreStageRef = useRef<HTMLDivElement>(null)
  const heroTextRef = useRef<HTMLDivElement>(null)
  const scene2Ref = useRef<HTMLDivElement>(null)
  const scene3Ref = useRef<HTMLDivElement>(null)
  const scene4Ref = useRef<HTMLDivElement>(null)

  const [hasAwakened, setHasAwakened] = useState(false)
  const [scrollProgressVal, setScrollProgressVal] = useState(0)

  // Awakening spark sequence timer
  useEffect(() => {
    const timer = setTimeout(() => {
      setHasAwakened(true)
    }, 500)
    return () => clearTimeout(timer)
  }, [])

  // =========================================================================
  // GSAP SCROLLTRIGGER PINNED STORY TIMELINE
  // =========================================================================
  useEffect(() => {
    const container = containerRef.current
    const pinStage = pinStageRef.current
    const coreStage = coreStageRef.current
    const heroText = heroTextRef.current
    const scene2 = scene2Ref.current
    const scene3 = scene3Ref.current
    const scene4 = scene4Ref.current

    if (!container || !pinStage || !coreStage || !heroText || !scene2 || !scene3 || !scene4) {
      return
    }

    const ctx = gsap.context(() => {
      // Main scrubbed timeline linked directly to window scroll
      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: container,
          start: 'top top',
          end: '+=3200',
          pin: pinStage,
          scrub: 0.8,
          anticipatePin: 1,
          invalidateOnRefresh: true,
          onUpdate: (self) => {
            setScrollProgressVal(self.progress)
          },
        },
      })

      // Set initial states
      gsap.set(coreStage, { x: '0vw', y: '0vh', scale: 1.05, opacity: 1 })
      gsap.set(heroText, { opacity: 1, y: 0, pointerEvents: 'auto' })
      gsap.set(scene2, { opacity: 0, x: -70, pointerEvents: 'none' })
      gsap.set(scene3, { opacity: 0, x: 70, pointerEvents: 'none' })
      gsap.set(scene4, { opacity: 0, y: 50, pointerEvents: 'none' })

      // =====================================================================
      // SEGMENT 1: Hero exits, Core travels diagonally RIGHT, Scene 2 enters LEFT
      // =====================================================================
      tl.to(heroText, {
        opacity: 0,
        y: -35,
        duration: 1.0,
        ease: 'power2.inOut',
        onComplete: () => {
          if (heroText) heroText.style.pointerEvents = 'none'
        },
        onReverseComplete: () => {
          if (heroText) heroText.style.pointerEvents = 'auto'
        },
      }, 0)
      .to(coreStage, {
        x: '30vw',
        y: '-2vh',
        scale: 0.95,
        duration: 2.0,
        ease: 'power2.inOut',
      }, 0)
      .to(scene2, {
        opacity: 1,
        x: 0,
        duration: 1.4,
        ease: 'power2.out',
        onStart: () => {
          if (scene2) scene2.style.pointerEvents = 'auto'
        },
        onReverseComplete: () => {
          if (scene2) scene2.style.pointerEvents = 'none'
        },
      }, 0.8)

      // Hold Scene 2 for readable pause
      tl.to({}, { duration: 1.0 })

      // =====================================================================
      // SEGMENT 2: Scene 2 exits, Core travels diagonally across to LEFT, Scene 3 enters RIGHT
      // =====================================================================
      tl.to(scene2, {
        opacity: 0,
        x: -40,
        duration: 1.0,
        ease: 'power2.in',
        onComplete: () => {
          if (scene2) scene2.style.pointerEvents = 'none'
        },
      })
      .to(coreStage, {
        x: '-30vw',
        y: '4vh',
        scale: 0.95,
        duration: 2.2,
        ease: 'power2.inOut',
      }, '<0.2')
      .to(scene3, {
        opacity: 1,
        x: 0,
        duration: 1.4,
        ease: 'power2.out',
        onStart: () => {
          if (scene3) scene3.style.pointerEvents = 'auto'
        },
        onReverseComplete: () => {
          if (scene3) scene3.style.pointerEvents = 'none'
        },
      }, '-=1.2')

      // Hold Scene 3 for readable pause
      tl.to({}, { duration: 1.0 })

      // =====================================================================
      // SEGMENT 3: Scene 3 exits, Core glides to CENTER-UPPER, Scene 4 enters
      // =====================================================================
      tl.to(scene3, {
        opacity: 0,
        x: 40,
        duration: 1.0,
        ease: 'power2.in',
        onComplete: () => {
          if (scene3) scene3.style.pointerEvents = 'none'
        },
      })
      .to(coreStage, {
        x: '0vw',
        y: '-22vh',
        scale: 0.74,
        duration: 2.0,
        ease: 'power2.inOut',
      }, '<0.2')
      .to(scene4, {
        opacity: 1,
        y: 0,
        duration: 1.4,
        ease: 'power2.out',
        onStart: () => {
          if (scene4) scene4.style.pointerEvents = 'auto'
        },
        onReverseComplete: () => {
          if (scene4) scene4.style.pointerEvents = 'none'
        },
      }, '-=1.2')

      // Hold Scene 4 before smoothly releasing the pin
      tl.to({}, { duration: 1.0 })
    }, container)

    return () => {
      ctx.revert()
    }
  }, [])

  return (
    <div 
      ref={containerRef} 
      className="relative w-full bg-transparent"
      id="hero-story-container"
    >
      {/* Pinned Viewport Stage: Pinned by ScrollTrigger over 3200px of scroll travel */}
      <div 
        ref={pinStageRef} 
        className="relative h-screen w-full overflow-hidden flex flex-col justify-between"
      >
        {/* SCENE A: AWAKENING SPARK REVEAL */}
        {!hasAwakened && (
          <div className="absolute inset-0 z-40 flex items-center justify-center pointer-events-none bg-[#090D16]">
            <div className="relative flex items-center justify-center animate-pulse">
              <div className="w-3.5 h-3.5 rounded-full bg-[#62CBE8] shadow-[0_0_20px_#62CBE8]" />
              <div className="absolute w-12 h-12 rounded-full border border-[#62CBE8]/40 animate-ping" />
            </div>
          </div>
        )}

        {/* Subtle Ambient Focal Glow */}
        <div 
          className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[540px] h-[300px] pointer-events-none"
          style={{
            background: 'radial-gradient(circle, rgba(98,203,232,0.06) 0%, transparent 65%)',
            filter: 'blur(50px)',
          }}
        />

        {/* Top Nav Spacer */}
        <div className="h-20 shrink-0" />

        {/* ================================================================= */}
        {/* MAIN STAGE: The Persistent 3D Object + Synchronized Texts         */}
        {/* ================================================================= */}
        <div className="relative flex-1 max-w-7xl mx-auto w-full px-6 flex items-center justify-center z-20">
          
          {/* =============================================================== */}
          {/* THE 3D PROTAGONIST: Yukti Core Möbius Loop & Gyroscope          */}
          {/* Physical transform manipulated directly by GSAP ScrollTrigger   */}
          {/* =============================================================== */}
          <div
            ref={coreStageRef}
            id="yukti-core-stage"
            className="absolute z-10 w-[420px] h-[420px] sm:w-[500px] sm:h-[500px] md:w-[560px] md:h-[560px] flex items-center justify-center pointer-events-none will-change-transform"
          >
            <div className="w-full h-full pointer-events-auto">
              <YuktiCoreScene 
                scrollProgress={scrollProgressVal} 
                isInteractive={true} 
              />
            </div>
          </div>

          {/* =============================================================== */}
          {/* 1. SCENE 1: CENTER HERO INTRO                                   */}
          {/* =============================================================== */}
          <div
            ref={heroTextRef}
            id="hero-scene-1"
            className="absolute inset-x-6 top-6 sm:top-10 text-center space-y-4 max-w-3xl mx-auto z-20 transition-opacity duration-300"
          >
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#111925] border border-[#263246] text-xs font-sans font-medium text-[#62CBE8]">
              <Sparkles className="w-3.5 h-3.5 text-[#62CBE8]" />
              <span>Engineering Operations Intelligence</span>
            </div>

            <h1 className="tracking-tight leading-tight">
              <YuktiWordmark size="hero" />
            </h1>

            <p className="font-display text-lg sm:text-2xl text-[#F1F5F9] tracking-wide font-normal">
              Your engineering work, <span className="text-[#62CBE8]">connected.</span>
            </p>

            <p className="text-sm sm:text-base text-[#A0AEC0] max-w-xl mx-auto font-sans leading-relaxed">
              YuktiOps connects team conversations, task dependencies, and GitHub activity to surface blockers, preserve project context, and help engineering teams move work forward with evidence-backed decisions.
            </p>

            {/* Hero CTAs */}
            <div className="flex flex-wrap items-center justify-center gap-3 pt-2 text-xs font-semibold">
              <button
                onClick={onEnterApp}
                className="px-5 py-2.5 bg-[#62CBE8] hover:bg-[#79D6EE] text-[#07131C] font-semibold rounded-lg flex items-center gap-2 transition-colors font-sans"
              >
                <span>Open Workspace</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
              <a
                href="#workflow"
                className="px-4 py-2.5 bg-[#111925] hover:bg-[#161F2D] text-[#F1F5F9] border border-[#263246] rounded-lg transition-colors font-sans flex items-center gap-1.5"
              >
                <span>Explore How It Works</span>
              </a>
            </div>

            {/* Scroll Indicator Prompt */}
            <div className="flex items-center justify-center gap-2 text-xs font-sans text-[#62CBE8]/90 pt-1">
              <span>Scroll to explore the architecture storyline</span>
              <ChevronDown className="w-4 h-4 animate-bounce" />
            </div>

            {/* Section 1 Horizontal Information Strip */}
            <div className="pt-1 max-w-lg mx-auto">
              <div className="bg-[#111925] border border-[#263246] rounded-xl px-5 py-2.5 shadow-lg flex items-center justify-between text-xs font-sans">
                <div className="flex items-center gap-1.5 text-[#62CBE8]">
                  <MessageSquare className="w-3.5 h-3.5" />
                  <span className="text-[#F1F5F9] font-medium">Conversations</span>
                </div>
                <span className="text-[#263246] font-bold">/</span>
                <div className="flex items-center gap-1.5 text-[#A0AEC0]">
                  <Kanban className="w-3.5 h-3.5" />
                  <span className="text-[#F1F5F9] font-medium">Tasks</span>
                </div>
                <span className="text-[#263246] font-bold">/</span>
                <div className="flex items-center gap-1.5 text-[#A0AEC0]">
                  <GitPullRequest className="w-3.5 h-3.5" />
                  <span className="text-[#F1F5F9] font-medium">GitHub</span>
                </div>
                <span className="text-[#263246] font-bold">/</span>
                <div className="flex items-center gap-1.5 text-[#62CBE8]">
                  <YuktiMark size={14} />
                  <span className="text-[#F1F5F9] font-medium">Intelligence</span>
                </div>
              </div>
            </div>
          </div>

          {/* =============================================================== */}
          {/* 2. SCENE 2: LEFT NARRATIVE (The Fragmentation Problem)           */}
          {/* =============================================================== */}
          <div
            ref={scene2Ref}
            id="hero-scene-2"
            className="absolute left-6 lg:left-12 max-w-md lg:max-w-lg z-20 space-y-5"
          >
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#E47777]/10 border border-[#E47777]/30 text-xs font-sans font-medium text-[#E47777]">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>01 // The Fragmentation Problem</span>
            </div>

            <h2 className="font-display text-xl sm:text-3xl text-white tracking-wide font-normal leading-snug">
              Your team&apos;s work is connected. <br />
              <span className="text-[#62CBE8]">Your tools aren&apos;t.</span>
            </h2>

            <p className="text-sm sm:text-base text-[#A0AEC0] leading-relaxed font-sans">
              Engineering conversations happen in chat channels, task backlogs live in issue trackers, and code commits push to GitHub.
            </p>

            <p className="text-sm text-[#A0AEC0] leading-relaxed font-sans">
              When an authentication dependency breaks, engineers mention it informally in chat, but task boards remain stale, leaving technical leads to chase outdated status updates.
            </p>

            <div className="p-4 rounded-xl bg-[#111925] border border-[#263246] space-y-2">
              <span className="text-[11px] font-sans font-semibold text-[#77869B] uppercase tracking-wider block">
                The Disconnect Gap
              </span>
              <div className="grid grid-cols-3 gap-2 text-center text-xs font-sans">
                <div className="p-2 rounded bg-[#090D16] border border-[#263246] text-[#A0AEC0]">
                  Chat Silos
                </div>
                <div className="p-2 rounded bg-[#090D16] border border-[#263246] text-[#A0AEC0]">
                  Stale Tasks
                </div>
                <div className="p-2 rounded bg-[#090D16] border border-[#263246] text-[#A0AEC0]">
                  Isolated Git
                </div>
              </div>
            </div>
          </div>

          {/* =============================================================== */}
          {/* 3. SCENE 3: RIGHT NARRATIVE (Every Signal Informs the Story)     */}
          {/* =============================================================== */}
          <div
            ref={scene3Ref}
            id="hero-scene-3"
            className="absolute right-6 lg:right-12 max-w-md lg:max-w-lg z-20 space-y-5"
          >
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#111925] border border-[#263246] text-xs font-sans font-medium text-[#62CBE8]">
              <Sparkles className="w-3.5 h-3.5 text-[#62CBE8]" />
              <span>02 // Unified Context</span>
            </div>

            <h2 className="font-display text-xl sm:text-3xl text-white tracking-wide font-normal leading-snug">
              Every signal informs <br />
              <span className="text-[#62CBE8]">
                the complete picture.
              </span>
            </h2>

            <p className="text-sm sm:text-base text-[#A0AEC0] leading-relaxed font-sans">
              YuktiOps unifies team discussions, task states, pull request reviews, and commit events into shared project context.
            </p>

            <p className="text-sm text-[#A0AEC0] leading-relaxed font-sans">
              When an engineer highlights a roadblock in English or supported Hinglish, natural language processing preserves the source quote as evidence and correlates it directly with active tasks and repository dependencies.
            </p>

            <div className="flex flex-wrap gap-2 pt-1 font-sans text-xs">
              <span className="px-2.5 py-1 rounded-md bg-[#161F2D] text-[#62CBE8] border border-[#263246]">
                Natural Language Processing
              </span>
              <span className="px-2.5 py-1 rounded-md bg-[#161F2D] text-[#A0AEC0] border border-[#263246]">
                GitHub Webhook Stream
              </span>
              <span className="px-2.5 py-1 rounded-md bg-[#161F2D] text-[#A0AEC0] border border-[#263246]">
                Project Memory
              </span>
            </div>
          </div>

          {/* =============================================================== */}
          {/* 4. SCENE 4: CENTER-LOWER DECISION STAGE (The Governed Workflow) */}
          {/* =============================================================== */}
          <div
            ref={scene4Ref}
            id="hero-scene-4"
            className="absolute inset-x-4 sm:inset-x-6 bottom-8 sm:bottom-12 max-w-3xl mx-auto z-20 space-y-4"
          >
            <div className="text-center space-y-2">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#38B982]/10 border border-[#38B982]/30 text-xs font-sans font-medium text-[#38B982]">
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>03 // Human-in-the-Loop Governance</span>
              </div>
              <h2 className="font-display text-lg sm:text-2xl text-white tracking-wide font-normal">
                From Raw Signals to Authorized Actions
              </h2>
              <p className="text-xs sm:text-sm text-[#A0AEC0] max-w-xl mx-auto font-sans">
                YuktiOps synthesizes recommendations with clear evidence, ensuring technical leads retain authoritative approval before changes apply.
              </p>
            </div>

            {/* Governed Resolution Proof Card */}
            <div className="p-4 sm:p-5 rounded-xl bg-[#111925] border border-[#263246] shadow-xl space-y-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#263246] pb-3 text-xs font-sans">
                <span className="text-[#62CBE8] flex items-center gap-1.5 font-semibold">
                  <CheckCircle2 className="w-4 h-4 text-[#38B982]" />
                  <span>Example Workflow: Dependency Blocker Resolution</span>
                </span>
                <span className="text-[#77869B]">Evidence Quote Attached · High Confidence Assessment</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                {/* Chat Evidence */}
                <div className="p-3 rounded-lg bg-[#090D16] border border-[#263246] space-y-1.5">
                  <span className="text-[10px] text-[#77869B] uppercase font-sans font-semibold">Source Signal (#frontend):</span>
                  <p className="text-[#F1F5F9] font-medium font-mono">
                    &quot;Login UI page done, but backend auth API nahi mila yet.&quot;
                  </p>
                  <span className="text-[10px] text-[#62CBE8] block font-sans">Author: Priya Sharma · Evaluated Conversation Signal</span>
                </div>

                {/* Lead Action */}
                <div className="p-3 rounded-lg bg-[#090D16] border border-[#263246] space-y-1.5">
                  <span className="text-[10px] text-[#77869B] uppercase font-sans font-semibold">Synthesized Recommendation:</span>
                  <p className="text-[#E5B85C] font-medium font-sans">
                    Mark <span className="font-mono">YUKTI-104</span> as BLOCKED (Dependency Missing)
                  </p>
                  <span className="text-[10px] text-[#38B982] block font-sans">Authorized Lead: Aarav Mehta · Review &amp; Approve → Audit Recorded</span>
                </div>
              </div>

              {/* CTAs */}
              <div className="pt-2 flex flex-wrap items-center justify-between gap-3 text-xs">
                <span className="text-[#77869B] font-sans text-xs">
                  All decisions recorded with timestamped audit history.
                </span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={onGoToLogin}
                    className="px-3.5 py-1.5 rounded-lg border border-[#263246] text-[#F1F5F9] hover:bg-[#161F2D] transition-colors font-sans"
                  >
                    Sign In
                  </button>
                  <button
                    onClick={onEnterApp}
                    className="px-4 py-1.5 rounded-lg bg-[#62CBE8] hover:bg-[#79D6EE] text-[#07131C] font-semibold flex items-center gap-1.5 transition-colors font-sans"
                  >
                    <span>Open Workspace</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          </div>

        </div>

        {/* Bottom Scroll Prompt Bar */}
        <div className="h-10 shrink-0 flex items-center justify-center text-xs font-sans text-[#77869B] tracking-normal z-20">
          <span>YuktiOps Architecture · Scroll Storyline</span>
        </div>
      </div>
    </div>
  )
}

export default CinematicHero
