import React, { useEffect, useRef, useState, useMemo } from 'react'
import * as THREE from 'three'
import { buildBracket, animateOpacity, type BracketResult } from './bracketBuilder'
import { DEMO_STAGES } from './landingData'

export const DemoViewer: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const bracketRef = useRef<BracketResult | null>(null)
  const isPlayingRef = useRef(true)
  const timeRef = useRef(0)
  const lastSolidRef = useRef(false)

  const [isPlaying, setIsPlaying] = useState(true)
  const [time, setTime] = useState(0)

  useEffect(() => {
    const container = containerRef.current
    const canvas = canvasRef.current
    if (!container || !canvas) return

    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(
      34,
      container.clientWidth / container.clientHeight,
      0.1,
      100,
    )
    camera.position.set(0, 0, 6.2)

    const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.setSize(container.clientWidth, container.clientHeight)

    const light1 = new THREE.DirectionalLight(0xffffff, 1.4)
    light1.position.set(5, 8, 5)
    scene.add(light1)

    const light2 = new THREE.DirectionalLight(0xaad8ff, 0.6)
    light2.position.set(-5, -3, -4)
    scene.add(light2)

    scene.add(new THREE.AmbientLight(0xffffff, 0.5))

    const group = new THREE.Group()
    group.rotation.x = 0.35
    group.rotation.y = -0.55
    scene.add(group)

    const bracket = buildBracket(group, {
      startOpacity: 0,
      markersHidden: true,
      wireColor: 0xffffff,
    })
    bracketRef.current = bracket

    let animId: number
    let lastTime = performance.now()

    function renderLoop(now: number) {
      animId = requestAnimationFrame(renderLoop)
      const dt = now - lastTime
      lastTime = now

      group.rotation.y += 0.003
      renderer.render(scene, camera)

      if (isPlayingRef.current) {
        let nextT = timeRef.current + dt
        if (nextT >= 12000) nextT = 0
        timeRef.current = nextT
        setTime(Math.floor(nextT))

        // Update stage mechanics
        let currentStageIdx = 0
        for (let i = DEMO_STAGES.length - 1; i >= 0; i--) {
          if (nextT >= DEMO_STAGES[i].t) {
            currentStageIdx = i
            break
          }
        }
        const stage = DEMO_STAGES[currentStageIdx]
        if (stage.solid !== lastSolidRef.current) {
          lastSolidRef.current = stage.solid
          animateOpacity(bracket, stage.solid)
        }
        bracket.markers.forEach((m, idx) => {
          m.visible = idx < stage.markers
        })
      }
    }
    renderLoop(performance.now())

    const onResize = () => {
      if (!container || !canvas) return
      camera.aspect = container.clientWidth / container.clientHeight
      camera.updateProjectionMatrix()
      renderer.setSize(container.clientWidth, container.clientHeight)
    }
    const resizeObserver = new ResizeObserver(onResize)
    resizeObserver.observe(container)

    return () => {
      cancelAnimationFrame(animId)
      resizeObserver.disconnect()
      renderer.dispose()
    }
  }, [])

  const currentStageIdx = useMemo(() => {
    for (let i = DEMO_STAGES.length - 1; i >= 0; i--) {
      if (time >= DEMO_STAGES[i].t) return i
    }
    return 0
  }, [time])

  const activeStage = DEMO_STAGES[currentStageIdx]
  const displaySeconds = Math.min(60, Math.floor((time / 12000) * 60))
  const progressPercent = (time / 12000) * 100

  const togglePlay = () => {
    const nxt = !isPlaying
    setIsPlaying(nxt)
    isPlayingRef.current = nxt
  }

  const handleScrubberClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect()
    const clickX = e.clientX - rect.left
    const ratio = Math.max(0, Math.min(1, clickX / rect.width))
    const nxtT = ratio * 12000
    timeRef.current = nxtT
    setTime(nxtT)

    let stageIdx = 0
    for (let i = DEMO_STAGES.length - 1; i >= 0; i--) {
      if (nxtT >= DEMO_STAGES[i].t) {
        stageIdx = i
        break
      }
    }
    const stage = DEMO_STAGES[stageIdx]
    if (bracketRef.current) {
      if (stage.solid !== lastSolidRef.current) {
        lastSolidRef.current = stage.solid
        animateOpacity(bracketRef.current, stage.solid)
      }
      bracketRef.current.markers.forEach((m, idx) => {
        m.visible = idx < stage.markers
      })
    }
  }

  return (
    <section className="demo-section" id="demo">
      <div className="landing-wrap">
        <div className="landing-section-heading landing-section-heading-centered landing-heading-on-dark reveal">
          <span className="landing-kicker landing-kicker-on-dark">See it in action</span>
          <h2>From CAD to clarity in minutes.</h2>
          <p>
            Watch the sample part move from raw geometry to process scores, mapped findings, and
            practical recommendations.
          </p>
        </div>

        <div className="demo-frame reveal is-visible">
          <div className="demo-chrome">
            <div className="demo-dots">
              <span />
              <span />
              <span />
            </div>
            <div className="demo-url">app.faberai.com/analysis/fa87e9a9</div>
          </div>
          <div className="demo-stage" ref={containerRef}>
            <canvas ref={canvasRef} id="demo-canvas" />
            <div
              className={`demo-verdict-pop ${activeStage.verdict ? 'show' : ''}`}
              id="demo-verdict"
            >
              35/100 · Injection molding recommended
            </div>
            <div className="demo-caption" id="demo-caption">
              <span className="step-tag" id="demo-step-tag">
                {activeStage.tag}
              </span>
              <span id="demo-step-text">{activeStage.text}</span>
            </div>
          </div>
          <div className="demo-controls">
            <button
              type="button"
              className="demo-play-btn"
              id="demo-play-btn"
              onClick={togglePlay}
              aria-label={isPlaying ? 'Pause' : 'Play'}
            >
              {isPlaying ? (
                <svg id="demo-icon-pause" width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <rect x="1" y="1" width="3.2" height="10" fill="white" />
                  <rect x="7.3" y="1" width="3.2" height="10" fill="white" />
                </svg>
              ) : (
                <svg id="demo-icon-play" width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <path d="M2 1L11 6L2 11V1Z" fill="white" />
                </svg>
              )}
            </button>
            <div
              className="demo-progress-track"
              role="slider"
              tabIndex={0}
              aria-valuenow={Math.round(progressPercent)}
              aria-valuemin={0}
              aria-valuemax={100}
              onClick={handleScrubberClick}
              style={{ cursor: 'pointer' }}
            >
              <div
                className="demo-progress-fill"
                id="demo-progress-fill"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
            <span className="demo-time" id="demo-time">
              0:{displaySeconds < 10 ? `0${displaySeconds}` : displaySeconds} / 0:12
            </span>
          </div>
        </div>
        <p className="demo-caption-note">
          This is an interactive product preview, not a decorative video placeholder.
        </p>
      </div>
    </section>
  )
}
