import {
  LuArrowRight,
  LuBox,
  LuChartNoAxesColumnIncreasing,
  LuCheck,
  LuCircleCheck,
  LuFileCheck2,
  LuLayers3,
  LuScanSearch,
  LuShieldCheck,
  LuUpload,
} from 'react-icons/lu'
import { Link } from 'react-router-dom'
import ModelPreview from '../ModelPreview/ModelPreview'
import BrandMark from '../layout/BrandMark'
import { InsideAppMockup } from './InsideAppMockup'
import { logoAnalysis } from './sampleAnalyses'

const credibilityItems = [
  {
    icon: LuBox,
    title: 'Molding + printing',
    detail: 'One part. Two process paths.',
  },
  {
    icon: LuFileCheck2,
    title: 'STEP / STP / STL',
    detail: 'Upload once. Inspect immediately.',
  },
  {
    icon: LuShieldCheck,
    title: 'Rule-level evidence',
    detail: 'Every score has a reason.',
  },
]

export function CredibilityStrip() {
  return (
    <section className="landing-credibility" aria-label="Platform capabilities">
      <div className="landing-wrap landing-credibility-glass">
        {credibilityItems.map(({ icon: Icon, title, detail }) => (
          <div className="landing-credibility-item" key={title}>
            <span className="landing-credibility-icon" aria-hidden="true">
              <Icon />
            </span>
            <span>
              <strong>{title}</strong>
              <small>{detail}</small>
            </span>
          </div>
        ))}
      </div>
    </section>
  )
}

const workflowSteps = [
  {
    number: '01',
    icon: LuUpload,
    title: 'Upload',
    text: 'Drop a production CAD file into the same workflow your team already uses.',
    visual: (
      <div className="landing-upload-mini">
        <LuBox />
        <strong>Drop a CAD file</strong>
        <span>.STEP &nbsp; .STP &nbsp; .STL</span>
      </div>
    ),
  },
  {
    number: '02',
    icon: LuScanSearch,
    title: 'Inspect',
    text: 'Geometry and manufacturing rules run together, then map findings onto the part.',
    visual: (
      <div className="landing-progress-mini">
        {['Geometry checks', 'Molding rules', 'Printing rules'].map((label) => (
          <div key={label}>
            <span>
              <LuCheck />
              {label}
            </span>
            <b>100%</b>
          </div>
        ))}
      </div>
    ),
  },
  {
    number: '03',
    icon: LuCircleCheck,
    title: 'Decide',
    text: 'Compare processes, understand the penalty behind every rule, and move with confidence.',
    visual: (
      <div className="landing-score-mini">
        <span>Overall score</span>
        <strong>
          35<small>/100</small>
        </strong>
        <div>
          <i />
        </div>
        <b>Needs review</b>
      </div>
    ),
  },
]

export function WorkflowSection() {
  return (
    <section className="landing-section landing-surface-section" id="workflow">
      <div className="landing-wrap">
        <div className="landing-section-heading landing-section-heading-centered reveal">
          <span className="landing-kicker">How it works</span>
          <h2>Three steps to better parts.</h2>
          <p>From raw geometry to a decision your engineering and supplier teams can both use.</p>
        </div>

        <div className="landing-workflow-line" aria-hidden="true" />
        <div className="landing-workflow-grid">
          {workflowSteps.map(({ number, icon: Icon, title, text, visual }) => (
            <article className="landing-workflow-step reveal" key={number}>
              <div className="landing-workflow-index">{number}</div>
              <div className="landing-workflow-copy">
                <Icon aria-hidden="true" />
                <h3>{title}</h3>
                <p>{text}</p>
              </div>
              <div className="landing-interactive-glass landing-workflow-visual">{visual}</div>
            </article>
          ))}
        </div>
      </div>
    </section>
  )
}

const proofPoints = [
  'Hundreds of molding and printing rules',
  'Visual issue mapping on real geometry',
  'Explainable penalties and practical fixes',
]

export function ProductProofSection() {
  return (
    <section className="landing-section landing-proof-section" id="product">
      <div className="landing-wrap landing-proof-grid">
        <div className="landing-proof-copy reveal">
          <span className="landing-kicker">Built for engineers</span>
          <h2>Answers you can act on.</h2>
          <p>
            Deep manufacturability evidence without the week-long review cycle. Change material,
            compare processes, and see why the score moved.
          </p>
          <ul>
            {proofPoints.map((point) => (
              <li key={point}>
                <LuCircleCheck />
                {point}
              </li>
            ))}
          </ul>
          <a className="landing-text-link" href="#report">
            Explore the sample report <LuArrowRight />
          </a>
        </div>
        <div className="landing-proof-app reveal">
          <InsideAppMockup />
          <aside className="landing-report-focus-glass" aria-label="Sample report summary">
            <span>DFM report</span>
            <div className="landing-report-score">
              <small>Overall score</small>
              <strong>
                35<em>/100</em>
              </strong>
              <i>
                <b />
              </i>
              <span>Needs review</span>
            </div>
            <div className="landing-report-issues">
              <small>Top issues</small>
              <p>
                <b>Wall thickness</b>
                <span>1,211 faces</span>
              </p>
              <p>
                <b>Draft angle</b>
                <span>28 faces</span>
              </p>
              <p>
                <b>Overhangs</b>
                <span>381 faces</span>
              </p>
            </div>
          </aside>
        </div>
      </div>
    </section>
  )
}

const moldingRows = [
  ['Overall score', '35 / 100', 'Needs review'],
  ['Wall thickness', '5 failed rules', 'Review'],
  ['Draft angle', '28 faces', 'Review'],
  ['Rib design', '5 of 5', 'Review'],
  ['Gate suggestions', '3', 'Recommended'],
]

const printingRows = [
  ['Overall score', '25 / 100', 'Not viable'],
  ['Minimum feature', '0.48 mm', 'Below minimum'],
  ['Overhangs', '381 faces', 'Review'],
  ['Support demand', '12.8%', 'Moderate'],
  ['Build envelope', '250 x 210 x 220', 'Pass'],
]

function ProcessColumn({
  icon: Icon,
  title,
  description,
  tone,
  rows,
}: {
  icon: typeof LuLayers3
  title: string
  description: string
  tone: 'molding' | 'printing'
  rows: string[][]
}) {
  const [[scoreLabel, scoreValue, scoreStatus], ...metrics] = rows

  return (
    <article className={`landing-process-column is-${tone}`}>
      <header>
        <div className="landing-process-identity">
          <span aria-hidden="true">
            <Icon />
          </span>
          <div>
            <h3>{title}</h3>
            <p>{description}</p>
          </div>
        </div>
        <div className="landing-process-score">
          <span>{scoreLabel}</span>
          <strong>{scoreValue}</strong>
          <em>{scoreStatus}</em>
        </div>
      </header>
      <div className="landing-process-metrics">
        {metrics.map(([label, value, status]) => (
          <p key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
            <em className={status === 'Pass' || status === 'Recommended' ? 'is-pass' : ''}>
              {status}
            </em>
          </p>
        ))}
      </div>
    </article>
  )
}

export function ProcessComparisonSection() {
  return (
    <section className="landing-section landing-surface-section landing-comparison" id="processes">
      <div className="landing-wrap landing-comparison-grid">
        <div className="landing-comparison-copy reveal">
          <div>
            <span className="landing-kicker">Molding vs. 3D printing</span>
            <h2>One part. Two manufacturing paths.</h2>
          </div>
          <div className="landing-comparison-summary">
            <p>
              See why the same geometry succeeds or fails differently before committing to a
              process.
            </p>
            <a className="landing-text-link" href="#report">
              View all rules <LuArrowRight />
            </a>
          </div>
        </div>
        <div className="landing-process-vessel reveal">
          <ProcessColumn
            icon={LuLayers3}
            title="Injection molding"
            description="Tooling-led production"
            tone="molding"
            rows={moldingRows}
          />
          <ProcessColumn
            icon={LuChartNoAxesColumnIncreasing}
            title="3D printing"
            description="Layer-built production"
            tone="printing"
            rows={printingRows}
          />
        </div>
      </div>
    </section>
  )
}

export function FinalCtaSection() {
  return (
    <section className="landing-final-cta" id="cta">
      <div className="landing-wrap landing-final-grid">
        <div className="landing-final-copy reveal">
          <span className="landing-kicker landing-kicker-on-dark">Ready when the CAD is.</span>
          <h2>
            Build better parts.
            <br />
            Start with clarity.
          </h2>
          <p>Reduce iterations, lower production risk, and hand suppliers evidence they can use.</p>
          <Link className="landing-button landing-button-primary" to="/login">
            Analyze a part <LuArrowRight />
          </Link>
        </div>

        <div className="landing-logo-scene reveal" aria-label="FaberAI 3D logo inspection">
          <div className="landing-logo-readout landing-logo-readout-score">
            <small>DFM score</small>
            <strong>87</strong>
            <span>Manufacturable</span>
          </div>
          <div className="landing-logo-readout landing-logo-readout-issues">
            <small>Critical issues</small>
            <strong>0</strong>
            <span>Ready</span>
          </div>
          <div className="landing-logo-readout landing-logo-readout-wall">
            <small>Wall thickness</small>
            <strong>1.8 mm</strong>
            <span>Pass</span>
          </div>
          <div className="landing-logo-model">
            <ModelPreview analysis={logoAnalysis} height="100%" markerRadius={0.075} />
          </div>
        </div>
      </div>
    </section>
  )
}

const footerGroups = [
  { title: 'Product', links: ['Overview', 'Features', 'Pricing', 'Updates'] },
  { title: 'Solutions', links: ['Injection molding', '3D printing', 'Design teams', 'Suppliers'] },
  { title: 'Resources', links: ['Documentation', 'Sample report', 'Help center', 'Security'] },
  { title: 'Company', links: ['About', 'Careers', 'Contact', 'Privacy'] },
]

export function FooterSection() {
  return (
    <footer className="landing-footer">
      <div className="landing-wrap">
        <div className="landing-footer-grid">
          <div className="landing-footer-brand">
            <BrandMark size={32} variant="full" />
            <p>Manufacturability clarity before production.</p>
          </div>
          {footerGroups.map((group) => (
            <nav key={group.title} aria-label={group.title}>
              <h3>{group.title}</h3>
              {group.links.map((link) => (
                <a href="#top" key={link}>
                  {link}
                </a>
              ))}
            </nav>
          ))}
        </div>
        <div className="landing-footer-bottom">
          <span>© 2026 FaberAI. All rights reserved.</span>
          <span>Terms of service &nbsp; Security &nbsp; Status</span>
        </div>
      </div>
    </footer>
  )
}
