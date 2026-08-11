import React, { useCallback, useEffect, useRef, useState } from 'react'
import * as THREE from 'three'
import { buildBracket, type BracketResult } from './bracketBuilder'
import { FINDINGS } from './landingData'

export const DeepDiveViewer: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const bracketRef = useRef<BracketResult | null>(null)
  const groupRef = useRef<THREE.Group | null>(null)
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null)

  const [activeIdx, setActiveIdx] = useState<number>(0)
  const [tooltip, setTooltip] = useState<{ visible: boolean; x: number; y: number }>({
    visible: true,
    x: 0,
    y: 0,
  })
  const selectFinding = useCallback((idx: number) => {
    setActiveIdx(idx)
  }, [])

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
    cameraRef.current = camera

    const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.setSize(container.clientWidth, container.clientHeight)

    const light1 = new THREE.DirectionalLight(0xffffff, 1.3)
    light1.position.set(5, 8, 5)
    scene.add(light1)

    const light2 = new THREE.DirectionalLight(0x7fa8db, 0.5)
    light2.position.set(-5, -3, -4)
    scene.add(light2)

    scene.add(new THREE.AmbientLight(0xffffff, 0.6))

    const group = new THREE.Group()
    group.rotation.x = 0.35
    group.rotation.y = -0.55
    scene.add(group)
    groupRef.current = group

    const bracket = buildBracket(group, {
      startOpacity: 0.85,
      wireColor: 0x243b53,
      markersHidden: false,
    })
    bracketRef.current = bracket

    let animId: number
    let dragging = false
    let lastX = 0
    let lastY = 0

    // Highlight initial marker (0)
    if (bracket.markers[0]) {
      bracket.markers[0].scale.set(1.4, 1.4, 1.4)
    }

    function renderLoop() {
      animId = requestAnimationFrame(renderLoop)
      if (!dragging) {
        group.rotation.y += 0.003
      }
      renderer.render(scene, camera)
    }
    renderLoop()

    const onPointerDown = (e: MouseEvent) => {
      dragging = true
      lastX = e.clientX
      lastY = e.clientY
    }

    const raycaster = new THREE.Raycaster()
    const mouse = new THREE.Vector2()

    const onPointerMove = (e: MouseEvent) => {
      if (!container) return
      const rect = container.getBoundingClientRect()
      if (dragging) {
        group.rotation.y += (e.clientX - lastX) * 0.01
        group.rotation.x += (e.clientY - lastY) * 0.01
        lastX = e.clientX
        lastY = e.clientY
        return
      }

      mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1
      mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1
      raycaster.setFromCamera(mouse, camera)

      const hits = raycaster.intersectObjects(bracket.markers)
      if (hits.length > 0 && hits[0].object instanceof THREE.Mesh) {
        const hit = hits[0].object
        const idx = hit.userData.findingIdx
        if (idx !== undefined) {
          canvas.style.cursor = 'pointer'
          if (e.type === 'click') {
            selectFinding(idx)
          }
        }
      } else {
        canvas.style.cursor = 'grab'
      }
    }

    const onClick = (e: MouseEvent) => {
      onPointerMove(e)
    }

    const onPointerUp = () => {
      dragging = false
    }

    canvas.style.cursor = 'grab'
    canvas.addEventListener('mousedown', onPointerDown)
    canvas.addEventListener('click', onClick)
    window.addEventListener('mousemove', onPointerMove)
    window.addEventListener('mouseup', onPointerUp)

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
      canvas.removeEventListener('mousedown', onPointerDown)
      canvas.removeEventListener('click', onClick)
      window.removeEventListener('mousemove', onPointerMove)
      window.removeEventListener('mouseup', onPointerUp)
      renderer.dispose()
    }
  }, [selectFinding])

  // Update marker highlight and tooltip position when activeIdx or rotation changes
  useEffect(() => {
    const updateTooltip = () => {
      const container = containerRef.current
      const bracket = bracketRef.current
      const group = groupRef.current
      const camera = cameraRef.current
      if (!container || !bracket || !group || !camera) return

      const marker = bracket.markers[activeIdx]
      if (!marker) return

      bracket.markers.forEach((m, idx) => {
        if (idx === activeIdx) m.scale.set(1.4, 1.4, 1.4)
        else m.scale.set(1, 1, 1)
      })

      const pos = marker.position.clone()
      group.localToWorld(pos)
      pos.project(camera)

      const rect = container.getBoundingClientRect()
      const x = ((pos.x + 1) * rect.width) / 2
      const y = ((-pos.y + 1) * rect.height) / 2
      setTooltip({ visible: true, x, y })
    }

    const interval = window.setInterval(updateTooltip, 30)
    return () => clearInterval(interval)
  }, [activeIdx])

  const currentFinding = FINDINGS[activeIdx] || FINDINGS[0]

  return (
    <section className="section deepdive">
      <div className="wrap">
        <div className="section-head reveal is-visible">
          <span className="eyebrow kicker-gap">
            <span className="dot"></span>See it work
          </span>
          <h2 className="section-title">See what FaberAI sees</h2>
          <p className="section-sub italic-voice">
            The same sample bracket from the report below — rotate it, resolve it from wireframe to
            solid, and click a marker to read the finding behind it.
          </p>
        </div>

        <div className="deepdive-grid">
          <div className="dd-viewer reveal is-visible">
            <div className="dd-canvas-wrap" ref={containerRef}>
              <canvas ref={canvasRef} id="dd-canvas" />
              <div
                className={`dd-finding-tip ${tooltip.visible && currentFinding ? 'show' : ''}`}
                id="dd-tip"
                style={{
                  left: `${tooltip.x}px`,
                  top: `${tooltip.y - 16}px`,
                  transform: 'translate(-50%, -100%)',
                }}
              >
                <b id="dd-tip-code">{currentFinding?.code || 'M1'}</b>
                <span id="dd-tip-text">{currentFinding?.text || ''}</span>
              </div>
            </div>
            <div className="dd-legend">
              <span>
                <i style={{ background: '#F5A623' }} />
                Minor / moderate finding
              </span>
              <span>
                <i style={{ background: '#E4572E' }} />
                Major finding
              </span>
            </div>
          </div>

          <div className="reveal reveal-delay-1 is-visible">
            <div className="findings-list" id="findings-list">
              {FINDINGS.map((f, index) => (
                <div
                  key={f.code}
                  className={`finding-row ${index === activeIdx ? 'active' : ''}`}
                  onClick={() => selectFinding(index)}
                  role="button"
                  tabIndex={0}
                >
                  <span className="fcode">{f.code}</span>
                  <div className="fbody">
                    <b>{f.title}</b>
                    <span>{f.text}</span>
                  </div>
                  <span className={`fimpact ${f.impact === 15 ? 'impact-15' : 'impact-5'}`}>
                    −{f.impact}
                  </span>
                </div>
              ))}
            </div>
            <p style={{ marginTop: '16px', fontSize: '12.5px', color: 'rgba(11,19,107,0.5)' }}>
              Showing 5 of 88 findings from this sample run · full detail in the PDF report below
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}
