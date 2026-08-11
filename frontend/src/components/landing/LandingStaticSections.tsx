import React from 'react'

export const LogoStrip: React.FC = () => {
  return (
    <>
      <section className="logo-strip">
        <div className="wrap">
          <p className="logo-strip-label">Built for teams shipping physical products</p>
          <div className="logo-row">
            <span className="logo-slot">Your logo</span>
            <span className="logo-slot">Your logo</span>
            <span className="logo-slot">Your logo</span>
            <span className="logo-slot">Your logo</span>
            <span className="logo-slot">Your logo</span>
          </div>
        </div>
      </section>
    </>
  )
}

export const OldNewSection: React.FC = () => {
  return (
    <>
      <section className="section" id="product">
        <div className="wrap">
          <div className="section-head reveal">
            <span className="eyebrow kicker-gap">
              <span className="dot"></span>The shift
            </span>
            <h2 className="section-title">DFM review used to be a bottleneck.</h2>
            <p className="section-sub italic-voice">
              Now it runs at the speed you actually design at.
            </p>
          </div>

          <div className="compare-grid">
            <div className="compare-col compare-old resolve-border reveal">
              <span className="tag">The old way</span>
              <h3>Send it out, wait, hope</h3>
              <ul className="compare-list">
                <li>File goes to a supplier or DFM specialist and sits in a queue</li>
                <li>Days pass before a markup comes back, often as loose PDF notes</li>
                <li>Feedback is qualitative — "thin here," with no face reference</li>
                <li>Every revision restarts the whole review cycle</li>
                <li>Knowledge of "what's actually moldable" lives in one person's head</li>
              </ul>
            </div>

            <div className="compare-arrow reveal reveal-delay-1">
              <svg width="34" height="34" viewBox="0 0 24 24" fill="none">
                <path
                  d="M4 12H20M20 12L14 6M20 12L14 18"
                  stroke="#0858F4"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>

            <div className="compare-col compare-new resolve-border is-solid reveal reveal-delay-2">
              <span className="tag">The FaberAI way</span>
              <h3>Upload it, know now</h3>
              <ul className="compare-list">
                <li>Drop in a STEP, STL, or native CAD file directly</li>
                <li>Scored analysis returns in under a minute, every time</li>
                <li>Every finding is tied to a specific face ID and ranked by impact</li>
                <li>Re-run instantly after each change — no queue, no wait</li>
                <li>Rules are explicit and consistent, not tribal knowledge</li>
              </ul>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}

export const WhoItsForSection: React.FC = () => {
  return (
    <>
      <section className="section" id="who">
        <div className="wrap">
          <div className="section-head reveal">
            <span className="eyebrow kicker-gap">
              <span className="dot"></span>Who it's for
            </span>
            <h2 className="section-title">Built into the moments that matter</h2>
            <p className="section-sub italic-voice">
              Same engine, different job depending on where you sit in the process.
            </p>
          </div>
          <div className="persona-grid">
            <div className="persona-card glass reveal">
              <div className="p-icon">
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                  <path
                    d="M2 15L9 2L16 15H2Z"
                    stroke="#0858F4"
                    strokeWidth="1.6"
                    strokeLinejoin="round"
                  />
                </svg>
              </div>
              <h3>Design engineers</h3>
              <p>
                Check manufacturability while the part is still easy to change — before it's frozen
                for review.
              </p>
            </div>
            <div className="persona-card glass reveal reveal-delay-1">
              <div className="p-icon">
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                  <rect
                    x="2"
                    y="2"
                    width="14"
                    height="14"
                    rx="2"
                    stroke="#0858F4"
                    strokeWidth="1.6"
                  />
                  <path d="M2 9H16" stroke="#0858F4" strokeWidth="1.6" />
                </svg>
              </div>
              <h3>Manufacturing engineers</h3>
              <p>
                Turn a vague "this needs work" into a ranked, face-referenced list you can hand back
                in minutes.
              </p>
            </div>
            <div className="persona-card glass reveal reveal-delay-2">
              <div className="p-icon">
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                  <path
                    d="M9 2L16 6V12L9 16L2 12V6L9 2Z"
                    stroke="#0858F4"
                    strokeWidth="1.6"
                    strokeLinejoin="round"
                  />
                </svg>
              </div>
              <h3>Hardware startups</h3>
              <p>
                Get supplier-grade DFM rigor without a full-time manufacturing engineer on staff
                yet.
              </p>
            </div>
            <div className="persona-card glass reveal reveal-delay-3">
              <div className="p-icon">
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                  <circle cx="9" cy="9" r="7" stroke="#0858F4" strokeWidth="1.6" />
                  <path d="M9 5V9L12 11" stroke="#0858F4" strokeWidth="1.6" strokeLinecap="round" />
                </svg>
              </div>
              <h3>Contract manufacturers</h3>
              <p>
                Screen incoming quote requests fast, and send back consistent, evidence-backed
                feedback.
              </p>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}

export const HowItWorksSection: React.FC = () => {
  return (
    <>
      <section className="section" id="how" style={{ background: '#F7F8FD' }}>
        <div className="wrap">
          <div className="section-head reveal">
            <span className="eyebrow kicker-gap">
              <span className="dot"></span>How it works
            </span>
            <h2 className="section-title">One upload, a complete manufacturability picture</h2>
            <p className="section-sub italic-voice">
              Every part gets checked against the same rules a shop floor would use — just faster,
              and on every face.
            </p>
          </div>

          <div className="capability-row glass reveal">
            <div className="capability-item">
              <svg width="22" height="22" viewBox="0 0 40 40" fill="none">
                <rect
                  x="5"
                  y="8"
                  width="13"
                  height="24"
                  rx="1"
                  stroke="#0858F4"
                  strokeWidth="1.8"
                />
                <rect
                  x="22"
                  y="14"
                  width="13"
                  height="18"
                  rx="1"
                  fill="#0858F4"
                  fillOpacity="0.14"
                  stroke="#0858F4"
                  strokeWidth="1.8"
                />
              </svg>
              <div>
                <b>Process fit scoring</b>
                <span>
                  Molding, printing, and more — each scored 0–100 with a confidence level.
                </span>
              </div>
            </div>
            <div className="capability-item">
              <svg width="22" height="22" viewBox="0 0 40 40" fill="none">
                <circle cx="12" cy="12" r="3.4" fill="#F5A623" />
                <circle cx="27" cy="16" r="3.4" fill="#F5A623" />
                <circle cx="17" cy="28" r="3.4" fill="#E4572E" />
              </svg>
              <div>
                <b>Face-by-face weak points</b>
                <span>Wall thickness, draft, ribs, bosses and overhangs, ranked by impact.</span>
              </div>
            </div>
            <div className="capability-item">
              <svg width="22" height="22" viewBox="0 0 40 40" fill="none">
                <path d="M20 4L34 12V28L20 36L6 28V12L20 4Z" stroke="#0858F4" strokeWidth="1.8" />
              </svg>
              <div>
                <b>Material-aware limits</b>
                <span>Rules tighten to your material — or flag it when one is assumed.</span>
              </div>
            </div>
          </div>

          <div className="steps">
            <div className="step reveal">
              <div className="step-line"></div>
              <div className="step-num">01</div>
              <h3>Upload</h3>
              <p>Drop in a STEP, STL, or native CAD file — no cleanup required first.</p>
            </div>
            <div className="step reveal reveal-delay-1">
              <div className="step-line"></div>
              <div className="step-num">02</div>
              <h3>Analyze</h3>
              <p>FaberAI runs manufacturing rule sets across every face, wall and feature.</p>
            </div>
            <div className="step reveal reveal-delay-2">
              <div className="step-line"></div>
              <div className="step-num">03</div>
              <h3>Score</h3>
              <p>
                Get a 0–100 rating per process, with a confidence level tied to what's known versus
                assumed.
              </p>
            </div>
            <div className="step reveal reveal-delay-3">
              <div className="step-num">04</div>
              <h3>Fix</h3>
              <p>Work through ranked, face-specific recommendations, then re-run in one click.</p>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}

export const RuleLibrarySection: React.FC = () => {
  return (
    <>
      <section className="section" id="rules">
        <div className="wrap">
          <div className="section-head reveal">
            <span className="eyebrow kicker-gap">
              <span className="dot"></span>Under the hood
            </span>
            <h2 className="section-title">Every check, named</h2>
            <p className="section-sub italic-voice">
              No "review geometry" black box — here's the actual rule set run against every part,
              organized by process.
            </p>
          </div>
          <div className="rule-lib-grid">
            <div className="rule-lib-col glass reveal">
              <div className="lib-head">
                <h3>Injection molding</h3>
                <span>7 rules</span>
              </div>
              <div className="rule-item">
                <span className="rcode">M1</span>
                <span className="rname">Minimum / maximum wall thickness</span>
              </div>
              <div className="rule-item">
                <span className="rcode">M2</span>
                <span className="rname">Wall thickness uniformity</span>
              </div>
              <div className="rule-item">
                <span className="rcode">M3</span>
                <span className="rname">Draft angle on vertical faces</span>
              </div>
              <div className="rule-item">
                <span className="rcode">M4</span>
                <span className="rname">Undercuts</span>
              </div>
              <div className="rule-item">
                <span className="rcode">M5</span>
                <span className="rname">Rib thickness ratio</span>
              </div>
              <div className="rule-item">
                <span className="rcode">M6</span>
                <span className="rname">Boss design</span>
              </div>
              <div className="rule-item">
                <span className="rcode">M7</span>
                <span className="rname">Tolerance feasibility</span>
              </div>
            </div>
            <div className="rule-lib-col glass reveal reveal-delay-1">
              <div className="lib-head">
                <h3>3D printing</h3>
                <span>6 rules</span>
              </div>
              <div className="rule-item">
                <span className="rcode">P1</span>
                <span className="rname">Overhang angle</span>
              </div>
              <div className="rule-item">
                <span className="rcode">P2</span>
                <span className="rname">Minimum feature size / thin walls</span>
              </div>
              <div className="rule-item">
                <span className="rcode">P3</span>
                <span className="rname">Support volume estimate</span>
              </div>
              <div className="rule-item">
                <span className="rcode">P4</span>
                <span className="rname">Aspect ratio / tall-thin stability</span>
              </div>
              <div className="rule-item">
                <span className="rcode">P5</span>
                <span className="rname">Trapped volumes / no drain</span>
              </div>
              <div className="rule-item">
                <span className="rcode">P6</span>
                <span className="rname">Bounding box vs. build envelope</span>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}

export const MetricsAndComparisonSection: React.FC = () => {
  return (
    <>
      <section className="section">
        <div className="wrap">
          <div className="section-head reveal">
            <span className="eyebrow kicker-gap">
              <span className="dot"></span>What changes
            </span>
            <h2 className="section-title">Weeks of back-and-forth, minutes of clarity</h2>
          </div>
          <div className="metrics-grid">
            <div className="metric-card feature glass reveal">
              <div className="from">Weeks per revision</div>
              <div className="to">
                &lt; <em>60 sec</em>
              </div>
              <div className="desc">
                Turnaround from upload to a scored, evidence-backed verdict — every time you re-run.
              </div>
            </div>
            <div className="metric-card glass reveal reveal-delay-1">
              <div className="from">One process, manually</div>
              <div className="to">
                <em>Multiple</em> processes
              </div>
              <div className="desc">
                Molding and printing scored side by side on the same geometry.
              </div>
            </div>
            <div className="metric-card glass reveal reveal-delay-2">
              <div className="from">Gut-feel confidence</div>
              <div className="to">
                Stated <em>%</em> confidence
              </div>
              <div className="desc">
                Every score names the assumptions behind it, not just a number.
              </div>
            </div>
            <div
              className="metric-card glass reveal reveal-delay-3"
              style={{ gridColumn: 'span 2' }}
            >
              <div className="from">General notes</div>
              <div className="to">
                <em>Face-level</em> evidence
              </div>
              <div className="desc">
                Findings cite the exact face ID and measured value, not "check walls."
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="section" style={{ paddingTop: '0' }}>
        <div className="wrap">
          <div className="section-head reveal">
            <span className="eyebrow kicker-gap">
              <span className="dot"></span>Side by side
            </span>
            <h2 className="section-title">Same review, two very different experiences</h2>
          </div>
          <div className="compare-table-wrap glass reveal">
            <table className="compare-table">
              <thead>
                <tr>
                  <th className="dim">Dimension</th>
                  <th>Manual DFM review</th>
                  <th className="col-faber">FaberAI</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <th>Turnaround</th>
                  <td className="dim">Days to weeks per revision</td>
                  <td className="col-faber">Under 60 seconds</td>
                </tr>
                <tr>
                  <th>Coverage</th>
                  <td className="dim">Reviewer's attention, part-dependent</td>
                  <td className="col-faber">Every face, every run, no fatigue</td>
                </tr>
                <tr>
                  <th>Consistency</th>
                  <td className="dim">Varies by reviewer and mood</td>
                  <td className="col-faber">Same rules, every time</td>
                </tr>
                <tr>
                  <th>Traceability</th>
                  <td className="dim">General written notes</td>
                  <td className="col-faber">Face ID, measured value, rule cited</td>
                </tr>
                <tr>
                  <th>Confidence</th>
                  <td className="dim">Implicit, rarely stated</td>
                  <td className="col-faber">Stated %, tied to assumptions</td>
                </tr>
                <tr>
                  <th>Re-check after a fix</th>
                  <td className="dim">Back of the queue</td>
                  <td className="col-faber">Instant, one click</td>
                </tr>
                <tr>
                  <th>Cost per revision</th>
                  <td className="dim">Billed hours or supplier turnaround</td>
                  <td className="col-faber">Included in your plan</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </>
  )
}

export const MidCtaAndFitSection: React.FC = () => {
  return (
    <>
      <section className="mid-cta">
        <div className="wrap">
          <div className="mid-cta-inner glass-tint reveal">
            <div className="mid-cta-text">
              <h3>See exactly where your part fails — before it costs you a mold.</h3>
              <p>Upload one part now. The first analysis is free, no CAD cleanup required.</p>
            </div>
            <a href="#cta" className="btn btn-primary">
              Upload a part
            </a>
          </div>
        </div>
      </section>

      <section className="section" id="fit" style={{ paddingTop: '0' }}>
        <div className="wrap">
          <div className="fit-grid">
            <div className="fit-col glass reveal">
              <h3>Works with the files you already have</h3>
              <div className="format-row">
                <span className="format-chip">.STEP</span>
                <span className="format-chip">.STL</span>
                <span className="format-chip">.IGES</span>
                <span className="format-chip">.SLDPRT</span>
                <span className="format-chip">.X_T</span>
                <span className="format-chip">Native CAD (via export)</span>
              </div>
            </div>
            <div className="fit-col glass reveal reveal-delay-1">
              <h3>Sits before the moment that's expensive to undo</h3>
              <div className="workflow-line">
                <span className="wf-step">Design</span>
                <svg width="14" height="14" viewBox="0 0 24 24">
                  <path
                    d="M4 12H20M20 12L14 6M20 12L14 18"
                    stroke="#0B136B"
                    strokeWidth="2"
                    fill="none"
                  />
                </svg>
                <span
                  className="wf-step"
                  style={{ background: 'rgba(8,88,244,0.16)', color: 'var(--primary)' }}
                >
                  FaberAI check
                </span>
                <svg width="14" height="14" viewBox="0 0 24 24">
                  <path
                    d="M4 12H20M20 12L14 6M20 12L14 18"
                    stroke="#0B136B"
                    strokeWidth="2"
                    fill="none"
                  />
                </svg>
                <span className="wf-step">Supplier RFQ</span>
                <svg width="14" height="14" viewBox="0 0 24 24">
                  <path
                    d="M4 12H20M20 12L14 6M20 12L14 18"
                    stroke="#0B136B"
                    strokeWidth="2"
                    fill="none"
                  />
                </svg>
                <span className="wf-step">Tooling</span>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}

export const TrustAndSecuritySection: React.FC = () => {
  return (
    <>
      <section className="section" id="trust" style={{ background: '#F7F8FD' }}>
        <div className="wrap">
          <div className="section-head reveal">
            <span className="eyebrow kicker-gap">
              <span className="dot"></span>Why trust it
            </span>
            <h2 className="section-title">Rules, not guesses</h2>
            <p className="section-sub italic-voice">
              AI does the heavy lifting on geometry — every verdict still traces back to a named,
              deterministic rule.
            </p>
          </div>
          <div className="trust-grid">
            <div className="trust-col glass reveal">
              <h3>
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                  <rect width="18" height="18" rx="4" fill="#0858F4" />
                </svg>
                What the AI handles
              </h3>
              <ul className="trust-ai">
                <li>Parses raw mesh or B-rep geometry from any uploaded CAD file</li>
                <li>
                  Clusters and classifies thousands of faces into walls, ribs, bosses, and drafts
                </li>
                <li>
                  Flags patterns — like abrupt thickness transitions — across the full part at once
                </li>
              </ul>
            </div>
            <div className="trust-col glass reveal reveal-delay-1">
              <h3>
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                  <rect
                    x="1"
                    y="1"
                    width="16"
                    height="16"
                    rx="4"
                    stroke="#0B136B"
                    strokeWidth="1.6"
                    strokeDasharray="2.4 2.4"
                  />
                </svg>
                What stays deterministic
              </h3>
              <ul className="trust-rules">
                <li>
                  Pass/fail thresholds are fixed, published manufacturing rules — not model output
                </li>
                <li>Confidence is computed from what was actually supplied vs. assumed</li>
                <li>Every finding names the rule, the face, and the measured value behind it</li>
              </ul>
              <div className="confidence-sample">
                Example, from the sample run:{' '}
                <b>
                  "No material supplied — generic engineering-thermoplastic limits were used and
                  confidence lowered accordingly."
                </b>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="section" id="security" style={{ background: '#F7F8FD' }}>
        <div className="wrap">
          <div className="section-head reveal">
            <span className="eyebrow kicker-gap">
              <span className="dot"></span>Your geometry, your IP
            </span>
            <h2 className="section-title">Built for parts you can't share loosely</h2>
            <p className="section-sub italic-voice">
              A CAD file is IP. FaberAI treats it that way by default.
            </p>
          </div>
          <div className="security-grid">
            <div className="security-card glass reveal">
              <svg className="s-icon" viewBox="0 0 32 32" fill="none">
                <rect
                  x="7"
                  y="14"
                  width="18"
                  height="13"
                  rx="2"
                  stroke="#0858F4"
                  strokeWidth="1.8"
                />
                <path d="M11 14V9a5 5 0 0110 0v5" stroke="#0858F4" strokeWidth="1.8" />
              </svg>
              <h3>Encrypted in transit and at rest</h3>
              <p>
                Uploaded files and generated reports are encrypted end-to-end, not just on the wire.
              </p>
            </div>
            <div className="security-card glass reveal reveal-delay-1">
              <svg className="s-icon" viewBox="0 0 32 32" fill="none">
                <circle cx="16" cy="16" r="11" stroke="#0858F4" strokeWidth="1.8" />
                <path
                  d="M11 16l4 4 7-8"
                  stroke="#0858F4"
                  strokeWidth="1.8"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              <h3>Never used to train models</h3>
              <p>
                Your geometry stays your geometry — it isn't used to train FaberAI or any
                third-party model.
              </p>
            </div>
            <div className="security-card glass reveal reveal-delay-2">
              <svg className="s-icon" viewBox="0 0 32 32" fill="none">
                <path
                  d="M16 5l10 4v7c0 6-4.2 10.5-10 11-5.8-.5-10-5-10-11V9l10-4z"
                  stroke="#0858F4"
                  strokeWidth="1.8"
                  strokeLinejoin="round"
                />
              </svg>
              <h3>Deletion on your schedule</h3>
              <p>
                Set an automatic retention window, or delete a file and its report the moment you're
                done with it.
              </p>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}

export const TestimonialsAndManifestoSection: React.FC = () => {
  return (
    <>
      <section className="section">
        <div className="wrap">
          <div
            className="section-head center reveal"
            style={{ marginLeft: 'auto', marginRight: 'auto' }}
          >
            <span className="eyebrow kicker-gap">
              <span className="dot"></span>From engineers
            </span>
            <h2 className="section-title">
              Trusted by people who'd normally distrust a tool like this
            </h2>
          </div>
          <div className="testi-grid">
            <div className="testi-card feature glass reveal">
              <p className="testi-quote">
                We used to wait a week for a DFM markup from our supplier. Now I get the same rigor
                before lunch, on every revision.
              </p>
              <div className="testi-person">
                <span className="testi-avatar"></span>
                <div>
                  <b>Manufacturing Engineer</b>
                  <span>Mid-size hardware startup</span>
                </div>
              </div>
            </div>
            <div className="testi-stack">
              <div className="testi-card glass reveal reveal-delay-1">
                <p className="testi-quote">
                  The confidence score changed how we brief suppliers. We know exactly what was
                  assumed before a single tool is cut.
                </p>
                <div className="testi-person">
                  <span className="testi-avatar"></span>
                  <div>
                    <b>Design Engineer</b>
                    <span>Industrial equipment manufacturer</span>
                  </div>
                </div>
              </div>
              <div className="testi-card glass reveal reveal-delay-2">
                <p className="testi-quote">
                  It caught wall-thickness issues our senior engineer would've flagged — in the
                  middle of an ordinary Tuesday sprint.
                </p>
                <div className="testi-person">
                  <span className="testi-avatar"></span>
                  <div>
                    <b>Mechanical Lead</b>
                    <span>Robotics team</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="manifesto">
        <div className="wrap">
          <div className="manifesto-inner reveal">
            <div className="manifesto-label">A belief we build around</div>
            <p className="manifesto-line">
              A part isn't finished when it looks right.
              <br />
              It's finished when it can be made.
            </p>
            <p className="manifesto-sub">FaberAI checks the second thing, automatically.</p>
          </div>
        </div>
      </section>
    </>
  )
}

export const FounderAndPricingSection: React.FC = () => {
  return (
    <>
      <section className="section" style={{ background: '#F7F8FD' }}>
        <div className="wrap">
          <div className="founder-note glass reveal">
            <span className="eyebrow kicker-gap">
              <span className="dot"></span>Why we built this
            </span>
            <p>
              We kept watching the same thing happen: a part would look finished, get sent out for
              quoting, and come back three weeks later with "this won't mold as designed." By then
              the schedule had already absorbed the delay.
            </p>
            <p>
              DFM knowledge isn't secret — it's just slow to access at the moment you actually need
              it, which is right before you hit export. So we built FaberAI to be that check: the
              same rules a manufacturing engineer would apply, run the instant you have a file, not
              the week after you've committed to it.
            </p>
            <div className="fn-sign">
              <span className="testi-avatar"></span>
              <div>
                <b>The FaberAI team</b>
                <span>Building the DFM check we wished we'd had</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="section" id="pricing">
        <div className="wrap">
          <div
            className="section-head center reveal"
            style={{ marginLeft: 'auto', marginRight: 'auto' }}
          >
            <span className="eyebrow kicker-gap">
              <span className="dot"></span>Pricing
            </span>
            <h2 className="section-title">Plans that scale with how much you upload</h2>
            <p className="section-sub italic-voice">
              Start free on a single part. Move up when checking parts becomes part of every
              revision.
            </p>
          </div>
          <div className="pricing-grid">
            <div className="pricing-card glass reveal">
              <h3>Starter</h3>
              <p className="p-sub">For trying it on a real part</p>
              <ul>
                <li>A handful of analyses per month</li>
                <li>Injection molding &amp; 3D printing scoring</li>
                <li>Full PDF report, every time</li>
              </ul>
              <a href="#cta" className="btn btn-ghost">
                Get started free
              </a>
            </div>
            <div className="pricing-card featured glass reveal reveal-delay-1">
              <span className="p-badge">Most teams</span>
              <h3>Team</h3>
              <p className="p-sub">For active design cycles</p>
              <ul>
                <li>Unlimited analyses for your team</li>
                <li>Material-specific rule tuning</li>
                <li>Shared report history &amp; comments</li>
                <li>Priority processing</li>
              </ul>
              <a href="#cta" className="btn btn-primary">
                Talk to us
              </a>
            </div>
            <div className="pricing-card glass reveal reveal-delay-2">
              <h3>Enterprise</h3>
              <p className="p-sub">For manufacturing orgs</p>
              <ul>
                <li>Custom rule sets &amp; material libraries</li>
                <li>API access for CAD-tool integration</li>
                <li>SSO, audit logs &amp; retention controls</li>
              </ul>
              <a href="#cta" className="btn btn-ghost">
                Contact sales
              </a>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}

export const FaqAndStatBandSection: React.FC = () => {
  return (
    <>
      <section className="section" id="faq" style={{ background: '#F7F8FD' }}>
        <div className="wrap" style={{ maxWidth: '820px' }}>
          <div className="section-head reveal">
            <span className="eyebrow kicker-gap">
              <span className="dot"></span>FAQ
            </span>
            <h2 className="section-title">Good questions, answered plainly</h2>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div className="glass faq-item reveal">
              <h3>What file formats can I upload?</h3>
              <p>
                STEP, STL, and most native CAD formats. Mesh files (STL) get a slightly lower
                confidence score than exact B-rep formats, and the report says so.
              </p>
            </div>
            <div className="glass faq-item reveal reveal-delay-1">
              <h3>What if I don't know the material yet?</h3>
              <p>
                FaberAI falls back to generic engineering-thermoplastic limits and lowers the
                confidence score — it never silently assumes the best case.
              </p>
            </div>
            <div className="glass faq-item reveal reveal-delay-2">
              <h3>Does this replace my DFM engineer?</h3>
              <p>
                No — it gives them a head start. Findings are ranked and evidence-backed so review
                time goes to judgment calls, not to finding the problems.
              </p>
            </div>
            <div className="glass faq-item reveal">
              <h3>Who can see my CAD file?</h3>
              <p>
                Only you and teammates you invite. Files aren't used to train any model, and you
                control how long they're retained.
              </p>
            </div>
            <div className="glass faq-item reveal reveal-delay-1">
              <h3>Do I need a contract to try it?</h3>
              <p>
                No — start on Starter with no commitment, and move to Team when checking parts
                becomes part of your regular workflow.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="stat-band">
        <div className="wrap">
          <div className="stat-band-grid">
            <div className="stat-band-item reveal">
              <b>1,211</b>
              <span>wall-thickness issues caught in a single sample run</span>
            </div>
            <div className="stat-band-item reveal reveal-delay-1">
              <b>88</b>
              <span>total findings surfaced, ranked by impact</span>
            </div>
            <div className="stat-band-item reveal reveal-delay-2">
              <b>6</b>
              <span>pages of evidence generated automatically</span>
            </div>
            <div className="stat-band-item reveal reveal-delay-3">
              <b>&lt;60s</b>
              <span>from upload to a scored verdict</span>
            </div>
          </div>
          <p className="stat-band-note">
            Figures from the sample analysis shown throughout this page — faberai-sample-part.stl,
            run fa87e9a9.
          </p>
        </div>
      </section>
    </>
  )
}

export const FinalCtaSection: React.FC = () => {
  return (
    <>
      <section className="section final-cta" id="cta">
        <div className="wrap">
          <div className="section-head reveal">
            <span className="eyebrow on-dark kicker-gap">
              <span className="dot"></span>Get started
            </span>
            <h2 className="section-title">Ready to see your part's score?</h2>
            <p className="section-sub italic-voice">
              Upload a CAD file and get a scored, evidence-backed manufacturability report back in
              minutes.
            </p>
          </div>
          <form
            className="cta-form glass-dark reveal"
            onSubmit={(e) => {
              e.preventDefault()
              const btn = e.currentTarget.querySelector('button')
              if (btn) btn.textContent = 'Request sent ✓'
            }}
          >
            <input type="email" placeholder="you@company.com" required />
            <button type="submit" className="btn btn-primary btn-sm">
              Request access
            </button>
          </form>
          <p className="cta-note">No spam. One email when your access is ready.</p>
        </div>
      </section>
    </>
  )
}

export const FooterSection: React.FC = () => {
  return (
    <>
      <footer>
        <div className="wrap">
          <div className="footer-grid">
            <div>
              <div className="footer-logo">
                <svg
                  className="logo-mark"
                  viewBox="0 0 40 40"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                  width="28"
                  height="28"
                >
                  <path
                    d="M4 14L18 6L34 15V15L20 23L4 14Z"
                    stroke="#FFFFFF"
                    strokeOpacity="0.6"
                    strokeWidth="1.4"
                    strokeDasharray="2.6 2.6"
                  />
                  <path d="M20 23L34 15V29L20 37V23Z" fill="#0858F4" />
                  <path d="M4 14L20 23V37L4 28V14Z" fill="#0858F4" fillOpacity="0.55" />
                </svg>
                FaberAI
              </div>
              <p style={{ maxWidth: '260px', fontSize: '13.5px', color: 'rgba(255,255,255,0.55)' }}>
                Manufacturability analysis for CAD files — process fit, weak points, and fixes, in
                minutes.
              </p>
              <div className="social-slot" style={{ marginTop: '18px' }}>
                <span>in</span>
                <span>X</span>
                <span>gh</span>
              </div>
            </div>
            <div className="footer-col">
              <h4>Product</h4>
              <ul>
                <li>
                  <a href="#product">Overview</a>
                </li>
                <li>
                  <a href="#how">How it works</a>
                </li>
                <li>
                  <a href="#inside">Inside the app</a>
                </li>
                <li>
                  <a href="#rules">Rule library</a>
                </li>
                <li>
                  <a href="#report">Sample report</a>
                </li>
                <li>
                  <a href="#pricing">Pricing</a>
                </li>
              </ul>
            </div>
            <div className="footer-col">
              <h4>Company</h4>
              <ul>
                <li>
                  <a href="#">About</a>
                </li>
                <li>
                  <a href="#">Careers</a>
                </li>
                <li>
                  <a href="#">Contact</a>
                </li>
              </ul>
            </div>
            <div className="footer-col">
              <h4>Resources</h4>
              <ul>
                <li>
                  <a href="#faq">FAQ</a>
                </li>
                <li>
                  <a href="#trust">Why trust it</a>
                </li>
                <li>
                  <a href="#security">Security</a>
                </li>
              </ul>
            </div>
          </div>
          <div className="footer-bottom">
            <span>© 2026 FaberAI. All rights reserved.</span>
            <span>Privacy · Terms</span>
          </div>
        </div>
      </footer>
    </>
  )
}
