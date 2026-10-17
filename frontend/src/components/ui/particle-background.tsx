import React, { useEffect, useRef } from 'react'

export type BackgroundIntensity = 'hero' | 'story' | 'subdued' | 'subtle' | 'restrained'

interface ParticleBackgroundProps {
  className?: string
  intensity?: BackgroundIntensity
  particleColor?: string
  lineColor?: string
}

export const ParticleBackground: React.FC<ParticleBackgroundProps> = ({
  className = '',
  intensity = 'hero',
  particleColor,
  lineColor,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null)

  // Configure parameters based on contextual intensity
  const config = (() => {
    switch (intensity) {
      case 'hero':
        return {
          divider: 16000,
          opacity: 0.55,
          defaultParticle: 'rgba(98, 203, 232, 0.35)',
          defaultLine: 'rgba(38, 50, 70, 0.25)',
          maxDistance: 110,
          speed: 0.22,
        }
      case 'story':
        return {
          divider: 19000,
          opacity: 0.45,
          defaultParticle: 'rgba(98, 203, 232, 0.25)',
          defaultLine: 'rgba(38, 50, 70, 0.18)',
          maxDistance: 95,
          speed: 0.18,
        }
      case 'subdued':
        return {
          divider: 23000,
          opacity: 0.35,
          defaultParticle: 'rgba(98, 203, 232, 0.18)',
          defaultLine: 'rgba(38, 50, 70, 0.12)',
          maxDistance: 85,
          speed: 0.14,
        }
      case 'subtle':
        return {
          divider: 27000,
          opacity: 0.25,
          defaultParticle: 'rgba(98, 203, 232, 0.14)',
          defaultLine: 'rgba(38, 50, 70, 0.08)',
          maxDistance: 75,
          speed: 0.1,
        }
      case 'restrained':
      default:
        return {
          divider: 32000,
          opacity: 0.18,
          defaultParticle: 'rgba(98, 203, 232, 0.10)',
          defaultLine: 'rgba(38, 50, 70, 0.05)',
          maxDistance: 65,
          speed: 0.08,
        }
    }
  })()

  const pColor = particleColor || config.defaultParticle
  const lColor = lineColor || config.defaultLine

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    let animationFrameId: number
    let isPaused = false

    // Respect user's reduced motion preferences
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    const prefersReducedMotion = mediaQuery.matches

    interface Particle {
      x: number
      y: number
      directionX: number
      directionY: number
      size: number
    }

    let particles: Particle[] = []

    const init = () => {
      particles = []
      const numberOfParticles = prefersReducedMotion
        ? Math.floor((canvas.height * canvas.width) / (config.divider * 2.5))
        : Math.floor((canvas.height * canvas.width) / config.divider)

      for (let i = 0; i < numberOfParticles; i++) {
        const size = Math.random() * 1.8 + 0.8
        const x = Math.random() * canvas.width
        const y = Math.random() * canvas.height
        const mult = prefersReducedMotion ? 0.05 : config.speed
        const directionX = (Math.random() - 0.5) * mult
        const directionY = (Math.random() - 0.5) * mult
        particles.push({ x, y, directionX, directionY, size })
      }
    }

    const resizeCanvas = () => {
      if (!canvas) return
      const parent = canvas.parentElement
      canvas.width = parent ? parent.clientWidth : window.innerWidth
      canvas.height = parent ? parent.clientHeight : window.innerHeight
      init()
    }

    window.addEventListener('resize', resizeCanvas)
    resizeCanvas()

    // Page Visibility API to pause animation while backgrounded
    const handleVisibilityChange = () => {
      if (document.hidden) {
        isPaused = true
        cancelAnimationFrame(animationFrameId)
      } else {
        isPaused = false
        animate()
      }
    }
    document.addEventListener('visibilitychange', handleVisibilityChange)

    const connect = () => {
      const maxDistSq = config.maxDistance * config.maxDistance
      for (let a = 0; a < particles.length; a++) {
        for (let b = a + 1; b < particles.length; b++) {
          const dx = particles[a].x - particles[b].x
          const dy = particles[a].y - particles[b].y
          const distSq = dx * dx + dy * dy

          if (distSq < maxDistSq) {
            const alpha = (1 - distSq / maxDistSq) * config.opacity
            ctx.strokeStyle = lColor.replace(/[\d.]+\)$/g, `${alpha.toFixed(3)})`)
            ctx.lineWidth = 0.8
            ctx.beginPath()
            ctx.moveTo(particles[a].x, particles[a].y)
            ctx.lineTo(particles[b].x, particles[b].y)
            ctx.stroke()
          }
        }
      }
    }

    const animate = () => {
      if (isPaused) return
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      for (let i = 0; i < particles.length; i++) {
        const p = particles[i]
        p.x += p.directionX
        p.y += p.directionY

        if (p.x > canvas.width) p.x = 0
        else if (p.x < 0) p.x = canvas.width
        if (p.y > canvas.height) p.y = 0
        else if (p.y < 0) p.y = canvas.height

        ctx.beginPath()
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2, false)
        ctx.fillStyle = pColor
        ctx.fill()
      }

      connect()
      animationFrameId = requestAnimationFrame(animate)
    }

    animate()

    return () => {
      window.removeEventListener('resize', resizeCanvas)
      document.removeEventListener('visibilitychange', handleVisibilityChange)
      cancelAnimationFrame(animationFrameId)
    }
  }, [config.divider, config.maxDistance, config.opacity, config.speed, lColor, pColor])

  return (
    <canvas
      ref={canvasRef}
      className={`absolute inset-0 pointer-events-none select-none z-0 ${className}`}
      style={{ display: 'block', width: '100%', height: '100%', opacity: config.opacity }}
      aria-hidden="true"
    />
  )
}

export default ParticleBackground
