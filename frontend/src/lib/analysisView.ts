import type { AnalysisResult, IssueSeverity, ManufacturabilityIssue } from '../types/analysis'

export interface DisplayIssue {
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

function fromRuleResult(rule: Record<string, unknown>): DisplayIssue | null {
  const status = getString(rule.status)?.toLowerCase()
  const findings = Array.isArray(rule.findings) ? rule.findings : []
  const failedLike = status === 'failed' || status === 'warning'

  if (!failedLike) return null

  const firstFinding = getRecord(findings[0])
  const ruleId = getString(rule.rule_id)
  const ruleName = getString(rule.rule_name) ?? ruleId ?? 'DFM rule'
  const measured = getNumber(rule.measured)
  const unit = getString(rule.unit)
  const impact = getNumber(rule.score_impact)
  const findingMessage = getString(firstFinding?.message)
  const findingRecommendation = getString(firstFinding?.recommendation)
  const message =
    findingMessage ??
    `${ruleName}${measured !== null ? ` measured ${measured}${unit ?? ''}` : ' needs review'}.`

  return {
    severity: normalizeSeverity(rule.severity),
    message,
    recommendation:
      findingRecommendation ??
      getString(rule.recommendation) ??
      (impact !== null
        ? `This rule affected the score by ${impact.toFixed(1)} points. Review the threshold details in the DFM report.`
        : 'Review the threshold details in the DFM report.'),
  }
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
    return rules
      .map((rule) => {
        const ruleRecord = getRecord(rule)
        return ruleRecord ? fromRuleResult(ruleRecord) : null
      })
      .filter((issue): issue is DisplayIssue => issue !== null)
  })

  if (reportIssues.length > 0) return reportIssues

  return Array.isArray(analysis.issues)
    ? analysis.issues.filter((issue) => isVisibleIssueSeverity(issue.severity)).map(fromLegacyIssue)
    : []
}
