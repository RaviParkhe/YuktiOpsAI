import React, { useRef, useEffect, useState } from 'react'
import * as THREE from 'three'

interface YuktiCoreSceneProps {
  className?: string
  scrollProgress?: number // 0 to 1
  isInteractive?: boolean
}

export const YuktiCoreScene: React.FC<YuktiCoreSceneProps> = ({
  className = '',
  scrollProgress = 0,
  isInteractive = true,
}) => {
  const mountRef = useRef<HTMLDivElement>(null)
  const [webGlSupported, setWebGlSupported] = useState(true)
  const sceneRef = useRef<{
    renderer?: THREE.WebGLRenderer
    animId?: number
    group?: THREE.Group
    mobiusMesh?: THREE.Mesh
    innerGlowRibbon?: THREE.Mesh
    outerGimbal?: THREE.Group
    innerGimbal?: THREE.Group
    centralCore?: THREE.Mesh
    wireCore?: THREE.Mesh
    dataPackets?: { mesh: THREE.Mesh; light: THREE.PointLight; speed: number; offset: number }[]
    mouseX: number
    mouseY: number
    targetRotX: number
    targetRotY: number
    isTabVisible: boolean
  }>({
    mouseX: 0,
    mouseY: 0,
    targetRotX: 0,
    targetRotY: 0,
    isTabVisible: true,
  })

  // Detect WebGL capability safely
  useEffect(() => {
    try {
      const canvas = document.createElement('canvas')
      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl')
      if (!gl) {
        setWebGlSupported(false)
      }
    } catch {
      setWebGlSupported(false)
    }
  }, [])

  // Update 3D orientation based on scroll progress
  useEffect(() => {
    if (!sceneRef.current.group) return
    const g = sceneRef.current.group
    // Continuous multi-axis rotation and pitch tied to scroll progression
    g.rotation.z = scrollProgress * Math.PI * 0.8
    g.rotation.y = scrollProgress * Math.PI * 1.6
    g.rotation.x = scrollProgress * Math.PI * 0.4
  }, [scrollProgress])

  // Mouse tilt tracking
  useEffect(() => {
    if (!isInteractive) return

    const handleMouseMove = (e: MouseEvent) => {
      const { innerWidth, innerHeight } = window
      const x = (e.clientX / innerWidth) * 2 - 1
      const y = -(e.clientY / innerHeight) * 2 + 1
      sceneRef.current.mouseX = x * 0.35
      sceneRef.current.mouseY = y * 0.35
    }

    const handleVisibilityChange = () => {
      sceneRef.current.isTabVisible = document.visibilityState === 'visible'
    }

    window.addEventListener('mousemove', handleMouseMove, { passive: true })
    document.addEventListener('visibilitychange', handleVisibilityChange)

    return () => {
      window.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [isInteractive])

  // Initialize Three.js Scene
  useEffect(() => {
    const container = mountRef.current
    if (!container || !webGlSupported) return

    const width = container.clientWidth || 500
    const height = container.clientHeight || 500

    // 1. Scene, Camera, Renderer
    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(42, width / height, 0.1, 100)
    camera.position.set(0, 0, 7.8)

    let renderer: THREE.WebGLRenderer
    try {
      renderer = new THREE.WebGLRenderer({
        antialias: true,
        alpha: true,
        powerPreference: 'high-performance',
      })
      renderer.setSize(width, height)
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
      renderer.toneMapping = THREE.ACESFilmicToneMapping
      renderer.toneMappingExposure = 1.2
      container.appendChild(renderer.domElement)
      sceneRef.current.renderer = renderer
    } catch {
      setWebGlSupported(false)
      return
    }

    // 2. Lighting System
    // Deep atmospheric ambient
    const ambientLight = new THREE.AmbientLight(0x090d16, 2.0)
    scene.add(ambientLight)

    // Key Light: Brand Cyan Directional Light
    const keyLight = new THREE.DirectionalLight(0x62cbe8, 2.8)
    keyLight.position.set(5, 7, 6)
    scene.add(keyLight)

    // Rim Light: Cool architectural edge illumination
    const rimLight = new THREE.DirectionalLight(0x79d6ee, 1.8)
    rimLight.position.set(-6, -4, -4)
    scene.add(rimLight)

    // Bottom Fill Light: Subtle slate bounce
    const fillLight = new THREE.DirectionalLight(0x263246, 1.2)
    fillLight.position.set(0, -6, 2)
    scene.add(fillLight)

    // Central Point Light inside the energy nucleus
    const centerPointLight = new THREE.PointLight(0x62cbe8, 2.6, 8, 1.4)
    centerPointLight.position.set(0, 0, 0)
    scene.add(centerPointLight)

    // Main Master Transform Group
    const masterGroup = new THREE.Group()
    scene.add(masterGroup)
    sceneRef.current.group = masterGroup

    // 3. Mathematical Möbius Ribbon Geometry
    const radius = 2.15
    const ribbonWidth = 0.58
    const segmentsU = 180
    const segmentsV = 14

    function createMobiusGeometry(r: number, w: number, segU: number, segV: number) {
      const geom = new THREE.BufferGeometry()
      const vertices: number[] = []
      const uvs: number[] = []
      const indices: number[] = []

      for (let i = 0; i <= segU; i++) {
        const u = (i / segU) * Math.PI * 2
        const halfTwist = u / 2
        // Undulating spatial center with gentle figure-8 wave
        const cx = r * Math.cos(u)
        const cy = r * Math.sin(u)
        const cz = 0.42 * Math.sin(u * 2)

        for (let j = 0; j <= segV; j++) {
          const v = (j / segV - 0.5) * w
          // Calculate surface point with half-twist rotation
          const ox = v * Math.cos(halfTwist) * Math.cos(u)
          const oy = v * Math.cos(halfTwist) * Math.sin(u)
          const oz = v * Math.sin(halfTwist) + cz

          vertices.push(cx + ox, cy + oy, oz)
          uvs.push(i / segU, j / segV)
        }
      }

      for (let i = 0; i < segU; i++) {
        for (let j = 0; j < segV; j++) {
          const a = i * (segV + 1) + j
          const b = (i + 1) * (segV + 1) + j
          const c = (i + 1) * (segV + 1) + (j + 1)
          const d = i * (segV + 1) + (j + 1)

          indices.push(a, b, d)
          indices.push(b, c, d)
        }
      }

      geom.setIndex(indices)
      geom.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3))
      geom.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2))
      geom.computeVertexNormals()
      return geom
    }

    const mobiusGeometry = createMobiusGeometry(radius, ribbonWidth, segmentsU, segmentsV)

    // Dark graphite metallic material with realistic roughness and micro-reflections
    const mobiusMaterial = new THREE.MeshStandardMaterial({
      color: 0x111925,
      roughness: 0.28,
      metalness: 0.88,
      side: THREE.DoubleSide,
      shadowSide: THREE.DoubleSide,
    })

    const mobiusMesh = new THREE.Mesh(mobiusGeometry, mobiusMaterial)
    masterGroup.add(mobiusMesh)
    sceneRef.current.mobiusMesh = mobiusMesh

    // Inner Glowing Core Trace (thin luminous track running along the ribbon)
    const glowTrackGeometry = createMobiusGeometry(radius, 0.045, segmentsU, 4)
    const glowTrackMaterial = new THREE.MeshStandardMaterial({
      color: 0x62cbe8,
      emissive: 0x62cbe8,
      emissiveIntensity: 1.3,
      roughness: 0.2,
      metalness: 0.1,
      side: THREE.DoubleSide,
    })
    const innerGlowRibbon = new THREE.Mesh(glowTrackGeometry, glowTrackMaterial)
    masterGroup.add(innerGlowRibbon)
    sceneRef.current.innerGlowRibbon = innerGlowRibbon

    // 4. Precision Gyroscope Gimbal Rings
    // Outer Gimbal Ring (Graphite with tick markers)
    const outerGimbalGroup = new THREE.Group()
    const outerRingGeom = new THREE.TorusGeometry(3.05, 0.035, 16, 128)
    const ringMaterial = new THREE.MeshStandardMaterial({
      color: 0x161f2d,
      roughness: 0.22,
      metalness: 0.92,
    })
    const outerRingMesh = new THREE.Mesh(outerRingGeom, ringMaterial)
    outerGimbalGroup.add(outerRingMesh)

    // Add 4 precision indicator notch blocks on outer ring
    for (let k = 0; k < 4; k++) {
      const notchAngle = (k * Math.PI) / 2
      const notchGeom = new THREE.BoxGeometry(0.08, 0.12, 0.1)
      const notchMat = new THREE.MeshStandardMaterial({
        color: 0x62cbe8,
        emissive: 0x62cbe8,
        emissiveIntensity: 0.8,
      })
      const notch = new THREE.Mesh(notchGeom, notchMat)
      notch.position.set(3.05 * Math.cos(notchAngle), 3.05 * Math.sin(notchAngle), 0)
      notch.rotation.z = notchAngle
      outerGimbalGroup.add(notch)
    }
    masterGroup.add(outerGimbalGroup)
    sceneRef.current.outerGimbal = outerGimbalGroup

    // Inner Gimbal Ring (Tilted at 55 degrees with graphite specular sheen)
    const innerGimbalGroup = new THREE.Group()
    const innerRingGeom = new THREE.TorusGeometry(2.72, 0.028, 16, 110)
    const innerRingMat = new THREE.MeshStandardMaterial({
      color: 0x161f2d,
      roughness: 0.24,
      metalness: 0.90,
    })
    const innerRingMesh = new THREE.Mesh(innerRingGeom, innerRingMat)
    innerGimbalGroup.add(innerRingMesh)
    innerGimbalGroup.rotation.x = Math.PI / 3.2
    innerGimbalGroup.rotation.y = Math.PI / 6
    masterGroup.add(innerGimbalGroup)
    sceneRef.current.innerGimbal = innerGimbalGroup

    // 5. Concentrated Central Energy Nucleus (Crystalline Faceted Icosahedron)
    const coreGeom = new THREE.IcosahedronGeometry(0.38, 0)
    const coreMat = new THREE.MeshStandardMaterial({
      color: 0x090d16,
      emissive: 0x62cbe8,
      emissiveIntensity: 1.8,
      roughness: 0.15,
      metalness: 0.4,
    })
    const centralCore = new THREE.Mesh(coreGeom, coreMat)
    masterGroup.add(centralCore)
    sceneRef.current.centralCore = centralCore

    // Outer subtle crystalline wireframe cage
    const wireGeom = new THREE.IcosahedronGeometry(0.55, 0)
    const wireMat = new THREE.MeshBasicMaterial({
      color: 0x62cbe8,
      wireframe: true,
      transparent: true,
      opacity: 0.35,
    })
    const wireCore = new THREE.Mesh(wireGeom, wireMat)
    masterGroup.add(wireCore)
    sceneRef.current.wireCore = wireCore

    // 6. Connected Signal Pulses along the Möbius path (3 Primary Signals)
    const signalColors = [0x62cbe8, 0x79d6ee, 0x62cbe8]
    const dataPackets: { mesh: THREE.Mesh; light: THREE.PointLight; speed: number; offset: number }[] = []

    signalColors.forEach((color, idx) => {
      const beadGeom = new THREE.SphereGeometry(0.045, 12, 12)
      const beadMat = new THREE.MeshBasicMaterial({ color })
      const bead = new THREE.Mesh(beadGeom, beadMat)

      const beadLight = new THREE.PointLight(color, 1.2, 2.0)
      bead.add(beadLight)

      masterGroup.add(bead)
      dataPackets.push({
        mesh: bead,
        light: beadLight,
        speed: 0.40 + idx * 0.06,
        offset: (idx * Math.PI * 2) / 3,
      })
    })
    sceneRef.current.dataPackets = dataPackets

    // 7. Handle Resize
    const handleResize = () => {
      if (!container || !renderer) return
      const newWidth = container.clientWidth || 500
      const newHeight = container.clientHeight || 500
      camera.aspect = newWidth / newHeight
      camera.updateProjectionMatrix()
      renderer.setSize(newWidth, newHeight)
    }

    const resizeObserver = new ResizeObserver(handleResize)
    resizeObserver.observe(container)

    // 8. Continuous Render Loop with visibility throttling
    let lastTime = performance.now()

    const animate = (currentTime: number) => {
      sceneRef.current.animId = requestAnimationFrame(animate)

      // Skip rendering if browser tab is hidden
      if (!sceneRef.current.isTabVisible) return

      const delta = Math.min((currentTime - lastTime) / 1000, 0.1)
      lastTime = currentTime

      // Smooth mouse tilt damping
      sceneRef.current.targetRotX += (sceneRef.current.mouseY - sceneRef.current.targetRotX) * 0.05
      sceneRef.current.targetRotY += (sceneRef.current.mouseX - sceneRef.current.targetRotY) * 0.05

      // Continuous Gyroscopic Precession & Mobius Rotation
      if (mobiusMesh) {
        mobiusMesh.rotation.y += 0.35 * delta
        mobiusMesh.rotation.x += 0.15 * delta
      }
      if (innerGlowRibbon) {
        innerGlowRibbon.rotation.y = mobiusMesh.rotation.y
        innerGlowRibbon.rotation.x = mobiusMesh.rotation.x
      }
      if (outerGimbalGroup) {
        outerGimbalGroup.rotation.z -= 0.18 * delta
        outerGimbalGroup.rotation.y += 0.08 * delta
      }
      if (innerGimbalGroup) {
        innerGimbalGroup.rotation.x += 0.22 * delta
        innerGimbalGroup.rotation.z += 0.14 * delta
      }
      if (centralCore) {
        centralCore.rotation.y -= 0.6 * delta
        centralCore.rotation.z += 0.4 * delta
      }
      if (wireCore) {
        wireCore.rotation.x += 0.5 * delta
        wireCore.rotation.y -= 0.3 * delta
      }

      // Apply mouse tilt to master group
      masterGroup.rotation.x = sceneRef.current.targetRotX
      masterGroup.rotation.y = sceneRef.current.targetRotY

      // Animate Light Signals Along the Mobius Strip Formula
      dataPackets.forEach((pkt) => {
        const t = (currentTime * 0.001 * pkt.speed + pkt.offset) % (Math.PI * 2)
        const halfTwist = t / 2
        const cx = radius * Math.cos(t)
        const cy = radius * Math.sin(t)
        const cz = 0.42 * Math.sin(t * 2)

        const v = 0 // Centered along width
        const ox = v * Math.cos(halfTwist) * Math.cos(t)
        const oy = v * Math.cos(halfTwist) * Math.sin(t)
        const oz = v * Math.sin(halfTwist) + cz

        pkt.mesh.position.set(cx + ox, cy + oy, oz)
      })

      renderer.render(scene, camera)
    }

    sceneRef.current.animId = requestAnimationFrame(animate)

    // 9. Cleanup
    return () => {
      resizeObserver.disconnect()
      if (sceneRef.current.animId) {
        cancelAnimationFrame(sceneRef.current.animId)
      }
      if (renderer) {
        renderer.dispose()
        if (renderer.domElement.parentElement) {
          renderer.domElement.parentElement.removeChild(renderer.domElement)
        }
      }
      mobiusGeometry.dispose()
      mobiusMaterial.dispose()
      glowTrackGeometry.dispose()
      glowTrackMaterial.dispose()
      outerRingGeom.dispose()
      innerRingGeom.dispose()
      ringMaterial.dispose()
      innerRingMat.dispose()
      coreGeom.dispose()
      coreMat.dispose()
      wireGeom.dispose()
      wireMat.dispose()
    }
  }, [webGlSupported])

  // Fallback for devices without WebGL
  if (!webGlSupported) {
    return (
      <div className={`relative flex items-center justify-center select-none ${className}`}>
        <div className="w-72 h-72 rounded-full border-2 border-[#65D8FF]/40 flex items-center justify-center relative shadow-[0_0_40px_rgba(101,216,255,0.2)]">
          <div className="w-56 h-56 rounded-full border border-[#9B8CFF]/50 animate-spin" />
          <div className="absolute w-20 h-20 rounded-xl bg-[#121824] border border-[#65D8FF] flex items-center justify-center shadow-xl">
            <span className="font-display text-xs text-[#65D8FF] font-bold">YUKTI</span>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div
      ref={mountRef}
      className={`relative w-full h-full flex items-center justify-center pointer-events-auto cursor-grab active:cursor-grabbing ${className}`}
      style={{ minHeight: '440px', minWidth: '320px' }}
      aria-label="Yukti Core 3D: Sculptural Möbius Loop and Gyroscope"
    />
  )
}

export default YuktiCoreScene
