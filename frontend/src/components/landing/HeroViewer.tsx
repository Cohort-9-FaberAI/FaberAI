import { useEffect, useState, type CSSProperties } from 'react'
import { LuArrowRight, LuCirclePlay, LuShieldCheck } from 'react-icons/lu'
import { Link } from 'react-router-dom'
import ModelPreview from '../ModelPreview/ModelPreview'
import { bracketAnalysis } from './sampleAnalyses'

const heroTagTracks = [
  [
    { label: 'DFM score', value: '35 / 100', detail: 'Needs review', tone: 'warning' },
    { label: 'Molding', value: '35 / 100', detail: '5 major findings', tone: 'warning' },
    { label: 'Part envelope', value: '90 x 60 x 51.5', detail: 'Millimeters', tone: 'blue' },
  ],
  [
    { label: 'Wall thickness', value: '100.83 mm', detail: 'Above 5.00 mm max', tone: 'danger' },
    { label: '3D printing', value: '25 / 100', detail: 'Overhang review', tone: 'danger' },
    { label: 'Draft angle', value: '0.0 deg', detail: 'Add at least 1.0 deg', tone: 'warning' },
  ],
  [
    { label: 'Mapped findings', value: '7 markers', detail: 'Pinned to geometry', tone: 'blue' },
    { label: 'Passed rules', value: '5 checks', detail: 'Evidence attached', tone: 'success' },
    { label: 'Analysis state', value: 'Complete', detail: 'Report ready', tone: 'success' },
  ],
] as const

const heroTagTimings = [
  { firstSwap: 3400, interval: 5700 },
  { firstSwap: 4700, interval: 6500 },
  { firstSwap: 5900, interval: 7300 },
] as const

export function HeroViewer() {
  const [tagIndices, setTagIndices] = useState([0, 0, 0])
  const [tagVisibility, setTagVisibility] = useState([true, true, true])

  useEffect(() => {
    const timeouts: number[] = []
    const intervals: number[] = []

    const swapTag = (slot: number) => {
      setTagVisibility((current) =>
        current.map((visible, index) => (index === slot ? false : visible)),
      )

      const contentTimeout = window.setTimeout(() => {
        setTagIndices((current) =>
          current.map((tagIndex, index) =>
            index === slot ? (tagIndex + 1) % heroTagTracks[index].length : tagIndex,
          ),
        )
        setTagVisibility((current) =>
          current.map((visible, index) => (index === slot ? true : visible)),
        )
      }, 480)

      timeouts.push(contentTimeout)
    }

    heroTagTimings.forEach(({ firstSwap, interval }, slot) => {
      const startTimeout = window.setTimeout(() => {
        swapTag(slot)
        intervals.push(window.setInterval(() => swapTag(slot), interval))
      }, firstSwap)

      timeouts.push(startTimeout)
    })

    return () => {
      intervals.forEach(window.clearInterval)
      timeouts.forEach(window.clearTimeout)
    }
  }, [])

  return (
    <header className="landing-hero" id="top">
      <div className="landing-hero-grid-overlay" aria-hidden="true" />
      <div className="landing-wrap landing-hero-grid">
        <div className="landing-hero-copy reveal is-visible">
          <span className="landing-kicker landing-kicker-on-dark">Manufacturing intelligence</span>
          <h1>Manufacturability clarity, before production.</h1>
          <p>
            FaberAI runs automated DFM analysis for molding and 3D printing, so you catch issues
            early, reduce iterations, and build right the first time.
          </p>
          <div className="landing-hero-actions">
            <Link to="/login" className="landing-button landing-button-primary">
              Analyze a part <LuArrowRight />
            </Link>
            <a href="#demo" className="landing-button landing-button-ghost-dark">
              See how it works <LuCirclePlay />
            </a>
          </div>
          <div className="landing-hero-trust">
            <LuShieldCheck />
            <span>Your CAD stays yours and is never used to train third-party models.</span>
          </div>
        </div>

        <div className="landing-hero-console landing-structural-glass reveal is-visible">
          <div className="landing-console-status" aria-hidden="true">
            <i /> Live sample analysis
          </div>
          <div className="landing-hero-model">
            <ModelPreview analysis={bracketAnalysis} height="100%" autoRotate />
          </div>

          <div
            className="landing-hero-floating-tags"
            aria-label="Live sample analysis measurements"
          >
            {heroTagTracks.map((track, index) => {
              const tag = track[tagIndices[index]]

              return (
                <div
                  className="landing-hero-floating-slot"
                  key={`hero-tag-${index}`}
                  style={
                    {
                      '--float-delay': `${index * -1.7}s`,
                      '--float-duration': `${5.6 + index * 0.8}s`,
                    } as CSSProperties
                  }
                >
                  <div
                    className={`landing-hero-floating-tag landing-focus-glass is-${tag.tone} ${
                      tagVisibility[index] ? 'is-visible' : 'is-changing'
                    }`}
                    aria-live="polite"
                  >
                    <small>{tag.label}</small>
                    <strong>{tag.value}</strong>
                    <span>{tag.detail}</span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </header>
  )
}
