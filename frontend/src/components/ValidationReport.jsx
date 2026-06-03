export default function ValidationReport({ report }) {
  if (!report) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">✅</div>
        <div className="empty-state-title">No validation report yet</div>
      </div>
    )
  }

  const passed = report.checks?.filter(c => c.passed).length || 0
  const failed = report.checks?.filter(c => !c.passed && !c.repaired).length || 0
  const repaired = report.checks?.filter(c => c.repaired).length || 0
  const total = report.checks?.length || 0
  const score = total > 0 ? Math.round((passed + repaired) / total * 100) : 0

  const scoreClass = score >= 90 ? 'high' : score >= 70 ? 'medium' : 'low'

  return (
    <div>
      <div className="validation-score">
        <div>
          <div className={`validation-score-value ${scoreClass}`}>{score}%</div>
          <div className="validation-score-label">Validation Score</div>
        </div>
        <div style={{ flex: 1, display: 'flex', gap: 'var(--space-4)', justifyContent: 'flex-end' }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 'var(--text-lg)', fontWeight: 700, color: 'var(--color-success)' }}>{passed}</div>
            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-tertiary)' }}>Passed</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 'var(--text-lg)', fontWeight: 700, color: 'var(--color-warning)' }}>{repaired}</div>
            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-tertiary)' }}>Repaired</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 'var(--text-lg)', fontWeight: 700, color: 'var(--color-error)' }}>{failed}</div>
            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-tertiary)' }}>Failed</div>
          </div>
        </div>
      </div>

      <div className="validation-list">
        {report.checks?.map((check, i) => (
          <div key={i} className="validation-item animate-fade-in" style={{ animationDelay: `${i * 0.05}s` }}>
            <div className={`validation-icon ${check.passed ? 'pass' : check.repaired ? 'repaired' : 'fail'}`}>
              {check.passed ? '✓' : check.repaired ? '🔧' : '✗'}
            </div>
            <span className="validation-item-text">
              {check.name}
              {check.message && (
                <span style={{ display: 'block', fontSize: 'var(--text-xs)', color: 'var(--color-text-tertiary)', marginTop: '2px' }}>
                  {check.message}
                </span>
              )}
              {check.repaired && check.repair_action && (
                <span style={{ display: 'block', fontSize: 'var(--text-xs)', color: 'var(--color-warning)', marginTop: '2px' }}>
                  🔧 {check.repair_action}
                </span>
              )}
            </span>
          </div>
        ))}
      </div>

      {report.repair_log?.length > 0 && (
        <div style={{ marginTop: 'var(--space-5)' }}>
          <h3 style={{ fontSize: 'var(--text-sm)', fontWeight: 600, marginBottom: 'var(--space-3)', color: 'var(--color-text-secondary)' }}>
            🔧 Repair Log
          </h3>
          <div style={{
            background: 'var(--color-bg-secondary)',
            borderRadius: 'var(--radius-md)',
            padding: 'var(--space-4)',
            fontFamily: 'var(--font-mono)',
            fontSize: 'var(--text-xs)',
            color: 'var(--color-text-tertiary)',
            lineHeight: 1.8,
          }}>
            {report.repair_log.map((log, i) => (
              <div key={i}>→ {log}</div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
