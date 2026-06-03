export default function MetricsPanel({ metrics }) {
  if (!metrics) return null

  const items = [
    {
      label: 'Total Time',
      value: metrics.total_duration_ms
        ? `${(metrics.total_duration_ms / 1000).toFixed(1)}s`
        : '—',
    },
    {
      label: 'Tokens Used',
      value: metrics.total_tokens
        ? metrics.total_tokens.toLocaleString()
        : '—',
    },
    {
      label: 'Est. Cost',
      value: metrics.estimated_cost_usd != null
        ? `$${metrics.estimated_cost_usd.toFixed(4)}`
        : '—',
    },
    {
      label: 'Repairs',
      value: metrics.repair_cycles != null
        ? metrics.repair_cycles.toString()
        : '—',
    },
    {
      label: 'Checks Passed',
      value: metrics.validation_checks_total
        ? `${metrics.validation_checks_passed}/${metrics.validation_checks_total}`
        : '—',
    },
    {
      label: 'Model',
      value: metrics.model_used || '—',
    },
  ]

  return (
    <div className="metrics-grid">
      {items.map((item, i) => (
        <div key={i} className="metric-card animate-fade-in" style={{ animationDelay: `${i * 0.05}s` }}>
          <div className="metric-value">{item.value}</div>
          <div className="metric-label">{item.label}</div>
        </div>
      ))}
    </div>
  )
}
