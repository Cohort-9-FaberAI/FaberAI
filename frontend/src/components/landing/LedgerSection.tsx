import React, { useEffect, useRef, useState } from 'react'

export const LedgerSection: React.FC = () => {
  const ledgerRef = useRef<HTMLDivElement>(null)
  const [animated, setAnimated] = useState(false)
  const [vals, setVals] = useState({ start: 0, m1: 0, m2: 0, m3: 0, m5: 0, m6: 0, final: 0 })

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !animated) {
          setAnimated(true)
        }
      },
      { threshold: 0.4 },
    )
    if (ledgerRef.current) observer.observe(ledgerRef.current)
    return () => observer.disconnect()
  }, [animated])

  useEffect(() => {
    if (!animated) return
    const dur = 700
    const targets = { start: 100, m1: -15, m2: -15, m3: -15, m5: -15, m6: -5, final: 35 }

    const startTime = performance.now()
    let frameId: number

    const animate = (now: number) => {
      const elapsed = now - startTime
      const progress = Math.min(1, elapsed / dur)
      const ease = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress)

      setVals({
        start: Math.round(targets.start * ease),
        m1: Math.round(targets.m1 * ease),
        m2: Math.round(targets.m2 * ease),
        m3: Math.round(targets.m3 * ease),
        m5: Math.round(targets.m5 * ease),
        m6: Math.round(targets.m6 * ease),
        final: Math.round(targets.final * ease),
      })

      if (progress < 1) {
        frameId = requestAnimationFrame(animate)
      }
    }

    frameId = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(frameId)
  }, [animated])

  return (
    <section className="section" id="scoring">
      <div className="wrap">
        <div
          className="section-head center reveal is-visible"
          style={{ marginLeft: 'auto', marginRight: 'auto' }}
        >
          <span className="eyebrow kicker-gap">
            <span className="dot"></span>No black box
          </span>
          <h2 className="section-title">Anatomy of a score</h2>
          <p className="section-sub italic-voice">
            Here&apos;s the actual arithmetic behind the 35/100 shown throughout this page — not a
            model&apos;s opinion, a sum.
          </p>
        </div>

        <div className="ledger-wrap" ref={ledgerRef}>
          <div className="ledger reveal is-visible">
            <div className="ledger-row start">
              <span className="lr-label">Starting score</span>
              <span className="lr-val">{vals.start}</span>
            </div>
            <div className="ledger-row deduct">
              <span className="lr-label">
                M1 · Wall thickness<span>1,211 issues, walls above material max</span>
              </span>
              <span className="lr-val">{vals.m1 === 0 ? '-0' : vals.m1}</span>
            </div>
            <div className="ledger-row deduct">
              <span className="lr-label">
                M2 · Wall uniformity<span>120 abrupt thickness transitions</span>
              </span>
              <span className="lr-val">{vals.m2 === 0 ? '-0' : vals.m2}</span>
            </div>
            <div className="ledger-row deduct">
              <span className="lr-label">
                M3 · Draft angle<span>28 of 28 vertical faces under 1.0°</span>
              </span>
              <span className="lr-val">{vals.m3 === 0 ? '-0' : vals.m3}</span>
            </div>
            <div className="ledger-row deduct">
              <span className="lr-label">
                M5 · Rib thickness ratio<span>5 of 5 ribs exceed 50% of wall</span>
              </span>
              <span className="lr-val">{vals.m5 === 0 ? '-0' : vals.m5}</span>
            </div>
            <div className="ledger-row deduct">
              <span className="lr-label">
                M6 · Boss design<span>2 of 12 bosses form a thick mass</span>
              </span>
              <span className="lr-val">{vals.m6 === 0 ? '-0' : vals.m6}</span>
            </div>
            <div className="ledger-row total">
              <span className="lr-label">Final score — injection molding</span>
              <span className="lr-val">{vals.final}/100</span>
            </div>
          </div>
          <p className="ledger-note">
            Confidence sits at <b>41%</b> on top of this — lowered because no material was supplied,
            so generic thermoplastic limits were assumed instead of your real values.
          </p>
        </div>
      </div>
    </section>
  )
}
