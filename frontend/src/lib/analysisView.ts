import type { AnalysisResult, IssueSeverity, ManufacturabilityIssue } from '../types/analysis'

export interface DisplayIssue {
  issue_id?: string
  severity: IssueSeverity
  message: string
  recommendation: string
}

function getRecord(value: unknown): Record<string, unknown> | null {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null
}

function getString(value: unknown): string | null {
  return typeof value === 'string' && value.trim() ? value : null
}

function getNumber(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null
}

function normalizeSeverity(value: unknown): IssueSeverity {
  const severity = getString(value)?.toLowerCase()
  if (
    severity === 'blocker' ||
    severity === 'major' ||
    severity === 'minor' ||
    severity === 'high' ||
    severity === 'medium' ||
    severity === 'low'
  ) {
    return severity
  }
  return 'medium'
}

function issueMessage(issue: ManufacturabilityIssue): string {
  return issue.message ?? issue.description ?? issue.title ?? 'Manufacturability issue'
}

function issueRecommendation(issue: ManufacturabilityIssue): string {
  return issue.recommendation ?? 'Review this feature against the highlighted DFM rule.'
}

function fromLegacyIssue(issue: ManufacturabilityIssue): DisplayIssue {
  return {
    issue_id: issue.issue_id,
    severity: normalizeSeverity(issue.severity),
    message: issueMessage(issue),
    recommendation: issueRecommendation(issue),
  }
}

export function isVisibleIssueSeverity(severity: unknown): boolean {
  const normalized = normalizeSeverity(severity)
  return (
    normalized === 'blocker' ||
    normalized === 'major' ||
    normalized === 'high' ||
    normalized === 'medium'
  )
}

function fromRuleResult(rule: Record<string, unknown>): DisplayIssue[] {
  const status = getString(rule.status)?.toLowerCase()
  const failedLike =
    status === 'failed' || status === 'fail' || status === 'warning' || status === 'warn'

  if (!failedLike) return []

  const ruleId = getString(rule.rule_id)
  const ruleName = getString(rule.rule_name) ?? ruleId ?? 'DFM rule'
  const measured = getNumber(rule.measured)
  const unit = getString(rule.unit)
  const impact = getNumber(rule.score_impact)
  const ruleRecommendation = getString(rule.recommendation)

  const findings = Array.isArray(rule.findings) ? rule.findings : []
  const resolvedFindings =
    findings.length > 0
      ? findings
      : [
          {
            severity: rule.severity,
            message: null,
            recommendation: ruleRecommendation,
            finding_id: ruleId,
          },
        ]

  const resolved: DisplayIssue[] = []
  for (const finding of resolvedFindings) {
    const fRec = getRecord(finding)
    if (!fRec) continue
    const findingMessage = getString(fRec.message)
    const findingRecommendation = getString(fRec.recommendation)
    resolved.push({
      issue_id: getString(fRec.finding_id) ?? ruleId ?? undefined,
      severity: normalizeSeverity(fRec.severity ?? rule.severity),
      message:
        findingMessage ??
        `${ruleName}${measured !== null ? ` measured ${measured}${unit ?? ''}` : ' needs review'}.`,
      recommendation:
        findingRecommendation ??
        ruleRecommendation ??
        (impact !== null
          ? `This rule affected the score by ${impact.toFixed(1)} points. Review the threshold details in the DFM report.`
          : 'Review the threshold details in the DFM report.'),
    })
  }
  return resolved
}

export function asAnalysisResult(value: Record<string, unknown> | null): AnalysisResult | null {
  return value as AnalysisResult | null
}

export function hasCompletedReport(analysis: AnalysisResult | null): boolean {
  return Boolean(analysis?.status === 'completed' && analysis.dfm_report)
}

export function getAnalysisScore(analysis: AnalysisResult | null): number | null {
  if (!analysis) return null
  if (typeof analysis.manufacturability_score === 'number') return analysis.manufacturability_score
  const report = getRecord(analysis.dfm_report)
  return getNumber(report?.manufacturability_score)
}

export function getDisplayIssues(analysis: AnalysisResult | null): DisplayIssue[] {
  if (!analysis) return []

  const report = getRecord(analysis.dfm_report)
  const processes = Array.isArray(report?.processes) ? report.processes : []
  const reportIssues = processes.flatMap((process) => {
    const processRecord = getRecord(process)
    const rules = Array.isArray(processRecord?.rule_results) ? processRecord.rule_results : []
    return rules.flatMap((rule) => {
      const ruleRecord = getRecord(rule)
      return ruleRecord ? fromRuleResult(ruleRecord) : []
    })
  })

  if (reportIssues.length > 0) return reportIssues

  return Array.isArray(analysis.issues) ? analysis.issues.map(fromLegacyIssue) : []
}

export function getMoldingScore(analysis: AnalysisResult | null): number | null {
  if (!analysis) return null
  if (typeof analysis.molding_score === 'number') return analysis.molding_score
  const report = getRecord(analysis.dfm_report)
  if (typeof report?.molding_score === 'number') return report.molding_score
  const processes = Array.isArray(report?.processes) ? report.processes : []
  for (const p of processes) {
    const pRec = getRecord(p)
    if (pRec?.process === 'injection_molding' || pRec?.process === 'molding') {
      const s = getNumber(pRec.score)
      if (s !== null) return s
    }
  }
  return null
}

export function getPrintingScore(analysis: AnalysisResult | null): number | null {
  if (!analysis) return null
  if (typeof analysis.printing_score === 'number') return analysis.printing_score
  const report = getRecord(analysis.dfm_report)
  if (typeof report?.printing_score === 'number') return report.printing_score
  const processes = Array.isArray(report?.processes) ? report.processes : []
  for (const p of processes) {
    const pRec = getRecord(p)
    if (pRec?.process === 'printing' || pRec?.process === '3d_printing') {
      const s = getNumber(pRec.score)
      if (s !== null) return s
    }
  }
  return null
}

export function getProcessIssues(
  analysis: AnalysisResult | null,
  processType: 'injection_molding' | 'printing',
): DisplayIssue[] {
  if (!analysis) return []

  const report = getRecord(analysis.dfm_report)
  const processes = Array.isArray(report?.processes) ? report.processes : []
  const matchingProcesses = processes.filter((proc) => {
    const pRec = getRecord(proc)
    if (!pRec?.process) return false
    if (processType === 'injection_molding') {
      return pRec.process === 'injection_molding' || pRec.process === 'molding'
    }
    return pRec.process === 'printing' || pRec.process === '3d_printing'
  })

  const reportIssues = matchingProcesses.flatMap((proc) => {
    const processRecord = getRecord(proc)
    const rules = Array.isArray(processRecord?.rule_results) ? processRecord.rule_results : []
    return rules.flatMap((rule) => {
      const ruleRecord = getRecord(rule)
      return ruleRecord ? fromRuleResult(ruleRecord) : []
    })
  })

  if (reportIssues.length > 0) return reportIssues
  return getDisplayIssues(analysis)
}

/**
 * Scope the 3D-viewport marker issues to a single process so markers match the
 * findings listed in the active tab. Falls back to the legacy report's
 * `analysis.issues` rule-id prefixes when the DFM report has no rule results.
 */
export function getMarkerIssuesForProcess(
  analysis: AnalysisResult | null,
  processType: 'injection_molding' | 'printing',
): ManufacturabilityIssue[] {
  if (!analysis) return []
  const issues = Array.isArray(analysis.issues) ? analysis.issues : []
  if (issues.length === 0) return issues

  const report = getRecord(analysis.dfm_report)
  const processes = Array.isArray(report?.processes) ? report.processes : []
  const ruleIds = new Set<string>()
  for (const proc of processes) {
    const pRec = getRecord(proc)
    if (!pRec?.process) continue
    const matches =
      processType === 'injection_molding'
        ? pRec.process === 'injection_molding' || pRec.process === 'molding'
        : pRec.process === 'printing' || pRec.process === '3d_printing'
    if (!matches) continue
    const rules = Array.isArray(pRec.rule_results) ? pRec.rule_results : []
    for (const rule of rules) {
      const rRec = getRecord(rule)
      const id = getString(rRec?.rule_id)
      if (id) ruleIds.add(id)
    }
  }

  if (ruleIds.size > 0) {
    return issues.filter((issue) => !issue.type || ruleIds.has(issue.type))
  }

  const prefix = processType === 'injection_molding' ? 'M' : 'P'
  return issues.filter(
    (issue) => !issue.type || String(issue.type).toUpperCase().startsWith(prefix),
  )
}

export function getScoreColor(score: number | null | undefined): string {
  if (score === null || score === undefined || !Number.isFinite(score)) return 'var(--text-h)'
  if (score >= 50) return '#66bb6a' // Green / Pro
  if (score >= 30) return '#ffb74d' // Amber / Neutral
  return '#ef5350' // Red / Fail
}

/**
 * Severity colours shared by the DFM analysis legend and the 3D issue
 * markers so both always render the same colours. Values mirror the CSS
 * custom properties `--severity-high/medium/low` in index.css.
 */
export const SEVERITY_COLORS = {
  severe: '#ef5350',
  problematic: '#ff7b00',
  minor: '#1aff00',
} as const

export function severityColor(severity: IssueSeverity | null | undefined): string {
  if (severity === 'blocker' || severity === 'high') return SEVERITY_COLORS.severe
  if (severity === 'major' || severity === 'medium') return SEVERITY_COLORS.problematic
  return SEVERITY_COLORS.minor
}
