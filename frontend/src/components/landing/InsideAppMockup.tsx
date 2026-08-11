import { useState } from 'react'
import BrandMark from '../layout/BrandMark'

export const InsideAppMockup = () => {
  const [material, setMaterial] = useState<string>('generic')

  const getMatData = (mat: string) => {
    switch (mat) {
      case 'abs':
        return {
          score: 48,
          offset: 98.0,
          caption: 'Needs review · 65% confidence',
          limit: '3.50 mm max',
          color: '#f5a623',
        }
      case 'nylon':
        return {
          score: 72,
          offset: 52.7,
          caption: 'Viable · 85% confidence',
          limit: '3.00 mm max',
          color: '#10b981',
        }
      case 'pp':
        return {
          score: 61,
          offset: 73.5,
          caption: 'Viable with edits · 70% confidence',
          limit: '4.00 mm max',
          color: '#3b82f6',
        }
      default:
        return {
          score: 35,
          offset: 122.5,
          caption: 'Needs review · 41% confidence',
          limit: '5.00 mm max',
          color: '#ef5350',
        }
    }
  }

  const data = getMatData(material)

  return (
    <div className="app-mockup reveal is-visible">
      <div
        className="demo-chrome"
        style={{ background: 'rgba(11,19,107,0.04)', borderBottomColor: 'rgba(11,19,107,0.08)' }}
      >
        <div className="demo-dots">
          <span style={{ background: 'rgba(11,19,107,0.15)' }} />
          <span style={{ background: 'rgba(11,19,107,0.15)' }} />
          <span style={{ background: 'rgba(11,19,107,0.15)' }} />
        </div>
        <div
          className="demo-url"
          style={{ color: 'rgba(11,19,107,0.4)', background: 'rgba(11,19,107,0.05)' }}
        >
          app.faberai.com/analysis/fa87e9a9
        </div>
      </div>
      <div className="app-shell">
        <div className="app-sidebar">
          <div className="app-logo">
            <BrandMark size={19} variant="full" />
          </div>
          <div className="app-nav-item">
            <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
              <rect x="1" y="1" width="6" height="6" rx="1" stroke="currentColor" />
              <rect x="8" y="1" width="6" height="6" rx="1" stroke="currentColor" />
              <rect x="1" y="8" width="6" height="6" rx="1" stroke="currentColor" />
              <rect x="8" y="8" width="6" height="6" rx="1" stroke="currentColor" />
            </svg>
            Projects
          </div>
          <div className="app-nav-item active">
            <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
              <path
                d="M2 13V2M2 13H13M5 13V8M8.5 13V5M12 13V3"
                stroke="currentColor"
                strokeWidth="1.4"
              />
            </svg>
            Analyses
          </div>
          <div className="app-nav-item">
            <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
              <circle cx="7.5" cy="5" r="2.5" stroke="currentColor" strokeWidth="1.4" />
              <path
                d="M2 13c0-3 2.5-4.5 5.5-4.5S13 10 13 13"
                stroke="currentColor"
                strokeWidth="1.4"
              />
            </svg>
            Team
          </div>
          <div className="app-nav-item">
            <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
              <circle cx="7.5" cy="7.5" r="2" stroke="currentColor" strokeWidth="1.4" />
              <path
                d="M7.5 1.5V3M7.5 12V13.5M13.5 7.5H12M3 7.5H1.5M11.8 3.2L10.7 4.3M4.3 10.7L3.2 11.8M11.8 11.8L10.7 10.7M4.3 4.3L3.2 3.2"
                stroke="currentColor"
                strokeWidth="1.4"
              />
            </svg>
            Settings
          </div>
        </div>
        <div className="app-main">
          <div className="app-topbar">
            <div className="app-breadcrumb">
              Projects / <b>faberai-sample-part.stl</b>
            </div>
            <div className="app-material-select">
              <label htmlFor="material-select">Material</label>
              <select
                id="material-select"
                value={material}
                onChange={(e) => setMaterial(e.target.value)}
              >
                <option value="generic">Generic engineering thermoplastic</option>
                <option value="abs">ABS</option>
                <option value="nylon">Nylon (PA6)</option>
                <option value="pp">Polypropylene</option>
              </select>
            </div>
          </div>
          <div className="app-body">
            <div className="app-scores">
              <div className="gauge-block">
                <svg className="gauge-svg" width="72" height="72" viewBox="0 0 72 72">
                  <circle className="gauge-track" cx="36" cy="36" r="30" />
                  <circle
                    className="gauge-fill"
                    id="gauge-fill-m"
                    cx="36"
                    cy="36"
                    r="30"
                    stroke={data.color}
                    strokeDasharray="188.5"
                    strokeDashoffset={data.offset}
                    style={{ transition: 'stroke-dashoffset 0.6s ease, stroke 0.6s ease' }}
                  />
                  <text className="gauge-num" id="gauge-num-m" x="36" y="41">
                    {data.score}
                  </text>
                </svg>
                <div className="g-label">
                  <b>Injection molding</b>
                  <span id="gauge-caption-m">{data.caption}</span>
                </div>
              </div>
              <div className="gauge-block">
                <svg className="gauge-svg" width="72" height="72" viewBox="0 0 72 72">
                  <circle className="gauge-track" cx="36" cy="36" r="30" />
                  <circle
                    className="gauge-fill"
                    cx="36"
                    cy="36"
                    r="30"
                    stroke="#a8a8b8"
                    strokeDasharray="188.5"
                    strokeDashoffset="141.6"
                  />
                  <text className="gauge-num" x="36" y="41" style={{ fill: '#6b6b85' }}>
                    25
                  </text>
                </svg>
                <div className="g-label">
                  <b>3D printing</b>
                  <span>Not viable · 63% confidence</span>
                </div>
              </div>
              <div className="app-confidence-note">
                Wall limit for selected material: <b id="wall-limit-note">{data.limit}</b> — every
                rule threshold below updates to match.
              </div>
            </div>
            <div className="app-findings">
              <div className="f-head">
                <h4>Top findings</h4>
                <span>88 total</span>
              </div>
              <div className="app-frow">
                <span className="fc">M1</span>
                <span className="ft">Wall on face 2815 exceeds material maximum</span>
                <span className="fi">+15</span>
              </div>
              <div className="app-frow">
                <span className="fc">M3</span>
                <span className="ft">28 of 28 vertical faces lack sufficient draft</span>
                <span className="fi">+15</span>
              </div>
              <div className="app-frow">
                <span className="fc">M5</span>
                <span className="ft">5 of 5 ribs exceed 50% of nominal wall</span>
                <span className="fi">+15</span>
              </div>
              <div className="app-frow">
                <span className="fc">P1</span>
                <span className="ft">381 overhanging faces past 45°</span>
                <span className="fi">+15</span>
              </div>
              <div className="app-frow">
                <span className="fc">M6</span>
                <span className="ft">2 of 12 bosses form a thick mass</span>
                <span className="fi">+5</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
