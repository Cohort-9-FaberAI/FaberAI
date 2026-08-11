export interface Finding {
  code: string
  title: string
  text: string
  impact: number
  sev: 'major' | 'minor'
}

export const FINDINGS: Finding[] = [
  {
    code: 'M1',
    title: 'Wall thickness',
    text: 'Wall on face 2815 measures 100.83 mm — above the 5.00 mm maximum for generic engineering thermoplastic. Core out the section to keep the wall uniform.',
    impact: 15,
    sev: 'major',
  },
  {
    code: 'M3',
    title: 'Draft angle',
    text: '28 of 28 vertical faces have less than 1.0° of draft. Apply at least 1.0° per side to every vertical wall.',
    impact: 15,
    sev: 'major',
  },
  {
    code: 'M5',
    title: 'Rib thickness ratio',
    text: '5 of 5 ribs exceed 50% of the nominal wall. Keep rib base thickness between 50–60% of the adjoining wall.',
    impact: 15,
    sev: 'major',
  },
  {
    code: 'M6',
    title: 'Boss design',
    text: '2 of 12 bosses form a thick mass. Hold boss walls to 40–60% of the nominal wall.',
    impact: 5,
    sev: 'minor',
  },
  {
    code: 'P1',
    title: 'Overhang angle',
    text: '381 overhanging faces past 45° (9.0% of surface area) in the −Y orientation. Keep down-facing surfaces within 45° of vertical where possible.',
    impact: 15,
    sev: 'major',
  },
]

export interface MaterialInfo {
  score: number
  confidence: number
  wall: string
  verdict: string
}

export const MATERIALS: Record<string, MaterialInfo> = {
  generic: { score: 35, confidence: 41, wall: '5.00 mm max', verdict: 'Needs review' },
  abs: { score: 58, confidence: 78, wall: '4.00 mm max', verdict: 'Feasible with changes' },
  nylon: { score: 64, confidence: 82, wall: '3.50 mm max', verdict: 'Feasible with changes' },
  pp: { score: 52, confidence: 74, wall: '4.50 mm max', verdict: 'Needs review' },
}

export const DEMO_STAGES = [
  {
    t: 0,
    tag: '01 · Upload',
    text: 'faberai-sample-part.stl arrives — no cleanup needed.',
    solid: false,
    markers: 0,
    verdict: false,
  },
  {
    t: 2600,
    tag: '02 · Analyze',
    text: 'Every face is checked against the rule library in real time.',
    solid: true,
    markers: 2,
    verdict: false,
  },
  {
    t: 6200,
    tag: '03 · Score',
    text: 'Molding and printing scored 0–100, each with a confidence level.',
    solid: true,
    markers: 5,
    verdict: true,
  },
  {
    t: 9600,
    tag: '04 · Fix',
    text: 'Ranked, face-specific recommendations — ready to act on.',
    solid: true,
    markers: 5,
    verdict: true,
  },
]
