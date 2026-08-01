import { useNavigate } from 'react-router-dom'

export default function LandingPage() {
  const navigate = useNavigate()

  const goToLogin = () => {
    navigate('/login')
  }

  return (
    <div>
      <div className="title-bar">
        <img className="title-image" src="/src/assets/FaberAI_logo.png" />
      </div>

      <div className="landing-bg">
        <div className="info-box">
          <h1>Quick and accurate AI review</h1>
          <ul>
            <li>
              How it works: AI parses the STL's mesh data — the triangular facets defining the
              model's surface — and runs geometric checks a human would otherwise do by eye.
            </li>
            <br />
            <li>3D printing checks:</li>
            <ul>
              <li>Overhangs beyond a safe angle (would sag without support)</li>
              <li>Walls thinner than the printer's minimum extrusion width</li>
              <li>Unsupported bridges</li>
              <li>Non-manifold geometry (holes, duplicate faces) that would confuse a slicer</li>
            </ul>
            <li>Injection molding checks:</li>
            <ul>
              <li>Draft angles needed for clean part ejection</li>
              <li>Uniform wall thickness (prevents warping or sink marks)</li>
              <li>Sharp internal corners (create stress concentrations)</li>
              <li>Undercuts that would require complex tooling</li>
            </ul>
            <br />
            <li>
              Scoring: Individual flaws are weighted by severity and frequency, then compressed into
              a single manufacturability score.
            </li>
            <li>
              Output: Gives designers a fast, at-a-glance read on how print- or mold-ready a file
              is, plus a prioritized list of exactly which regions to fix before production.
            </li>
          </ul>
        </div>
        <div>
          <img src="/src/assets/landingPage.png" className="landing-img" />
          <div className="button-box">
            <button onClick={goToLogin}>Get Started</button>
          </div>
        </div>
      </div>
    </div>
  )
}
