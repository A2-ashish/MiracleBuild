import { useState } from 'react'
import { generateMockData } from '../runtime/MockDataEngine'

export default function RuntimePreview({ config }) {
  const [activePage, setActivePage] = useState(0)

  if (!config?.ui) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">🚀</div>
        <div className="empty-state-title">No preview available</div>
      </div>
    )
  }

  const { ui, database, auth } = config
  const pages = ui.pages || []
  const navItems = ui.navigation?.items || []
  const currentPage = pages[activePage] || pages[0]
  const theme = ui.theme || {}
  const colors = theme.colors || {}

  return (
    <div className="runtime-preview">
      <div className="runtime-preview-bar">
        <div className="runtime-preview-dot red" />
        <div className="runtime-preview-dot yellow" />
        <div className="runtime-preview-dot green" />
        <div className="runtime-preview-url">
          localhost:3000{currentPage?.path || '/'}
        </div>
      </div>
      <div className="runtime-preview-content" style={{
        display: 'flex',
        minHeight: 500,
        fontFamily: theme.font_family || 'Inter, sans-serif',
        fontSize: 13,
        background: colors.background || '#0f172a',
        color: colors.text || '#f8fafc',
      }}>
        {/* Sidebar */}
        <div style={{
          width: 200,
          background: colors.surface || '#1e293b',
          borderRight: `1px solid ${colors.surface || '#334155'}33`,
          padding: '16px 0',
          flexShrink: 0,
          display: 'flex',
          flexDirection: 'column',
        }}>
          <div style={{
            padding: '0 16px 16px',
            fontWeight: 700,
            fontSize: 15,
            color: colors.primary || '#6366f1',
            borderBottom: '1px solid rgba(255,255,255,0.06)',
            marginBottom: 8,
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}>
            <span style={{
              width: 28, height: 28, borderRadius: 8,
              background: `linear-gradient(135deg, ${colors.primary || '#6366f1'}, ${colors.secondary || '#8b5cf6'})`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 12, color: 'white',
            }}>
              {ui.app_name?.[0] || 'A'}
            </span>
            {ui.app_name || 'App'}
          </div>

          {navItems.map((item, i) => (
            <button key={i}
              onClick={() => { const idx = pages.findIndex(p => p.path === item.path); if (idx >= 0) setActivePage(idx) }}
              style={{
                display: 'flex', alignItems: 'center', gap: 10, padding: '10px 16px',
                background: pages[activePage]?.path === item.path ? `${colors.primary || '#6366f1'}20` : 'transparent',
                border: 'none',
                borderRight: pages[activePage]?.path === item.path ? `3px solid ${colors.primary || '#6366f1'}` : '3px solid transparent',
                color: pages[activePage]?.path === item.path ? (colors.primary || '#6366f1') : (colors.text_secondary || '#94a3b8'),
                cursor: 'pointer', fontSize: 13, fontFamily: 'inherit', textAlign: 'left', width: '100%', transition: 'all 0.15s',
              }}
            >
              <span style={{ fontSize: 15 }}>{item.icon || '📄'}</span>
              {item.label}
            </button>
          ))}

          <div style={{
            marginTop: 'auto', padding: '12px 16px',
            borderTop: '1px solid rgba(255,255,255,0.06)',
            display: 'flex', alignItems: 'center', gap: 8, fontSize: 12,
            color: colors.text_secondary || '#94a3b8',
          }}>
            <div style={{
              width: 28, height: 28, borderRadius: '50%',
              background: `linear-gradient(135deg, ${colors.secondary || '#8b5cf6'}, ${colors.accent || '#06b6d4'})`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 11, color: 'white', fontWeight: 600,
            }}>AD</div>
            <div>
              <div style={{ fontWeight: 500, color: colors.text || '#f8fafc' }}>Admin User</div>
              <div style={{ fontSize: 11 }}>{auth?.roles?.[0]?.name || 'admin'}</div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div style={{ flex: 1, padding: 24, overflow: 'auto' }}>
          {currentPage && <PageRenderer page={currentPage} database={database} colors={colors} />}
        </div>
      </div>
    </div>
  )
}

function PageRenderer({ page, database, colors }) {
  return (
    <div>
      <div style={{ marginBottom: 20 }}>
        <h1 style={{ fontSize: 20, fontWeight: 700, margin: 0 }}>{page.title}</h1>
        <div style={{ fontSize: 12, color: colors.text_secondary || '#94a3b8', marginTop: 4 }}>
          {page.path}
          {page.allowed_roles?.length > 0 && (
            <span style={{ marginLeft: 8, padding: '2px 8px', background: 'rgba(99,102,241,0.15)', borderRadius: 12, fontSize: 11 }}>
              {page.allowed_roles.join(', ')}
            </span>
          )}
        </div>
      </div>
      <div style={{
        display: 'grid',
        gridTemplateColumns: page.layout === 'dashboard' ? 'repeat(auto-fit, minmax(280px, 1fr))' : '1fr',
        gap: 16,
      }}>
        {page.components?.map((comp, i) => (
          <ComponentRenderer key={i} component={comp} database={database} colors={colors} />
        ))}
      </div>
    </div>
  )
}

function ComponentRenderer({ component, database, colors }) {
  const card = {
    background: `${colors.surface || '#1e293b'}99`,
    border: '1px solid rgba(255,255,255,0.06)',
    borderRadius: 12, overflow: 'hidden',
    gridColumn: component.grid_span === 12 ? '1 / -1' : 'auto',
  }
  const hdr = {
    padding: '14px 16px', borderBottom: '1px solid rgba(255,255,255,0.06)',
    fontWeight: 600, fontSize: 14, display: 'flex', alignItems: 'center', justifyContent: 'space-between',
  }

  switch (component.type) {
    case 'stat_card': return <StatCardPreview component={component} colors={colors} style={card} />
    case 'table': return (
      <div style={card}>
        <div style={hdr}>
          {component.title || 'Data Table'}
          <button style={{ padding: '4px 12px', background: colors.primary || '#6366f1', border: 'none', borderRadius: 6, color: 'white', fontSize: 12, cursor: 'pointer' }}>+ Add New</button>
        </div>
        <TablePreview component={component} database={database} colors={colors} />
      </div>
    )
    case 'form': return (
      <div style={card}>
        <div style={hdr}>{component.title || 'Form'}</div>
        <div style={{ padding: 16 }}><FormPreview component={component} colors={colors} /></div>
      </div>
    )
    case 'chart': return (
      <div style={card}>
        <div style={hdr}>{component.title || 'Chart'}</div>
        <div style={{ padding: 16 }}><ChartPreview component={component} colors={colors} /></div>
      </div>
    )
    case 'list': return (
      <div style={card}>
        <div style={hdr}>{component.title || 'List'}</div>
        <div style={{ padding: 16 }}><ListPreview component={component} colors={colors} /></div>
      </div>
    )
    default: return (
      <div style={card}>
        <div style={hdr}>{component.title || component.type}</div>
        <div style={{ padding: 32, color: colors.text_secondary, fontSize: 12, textAlign: 'center' }}>{component.type} component</div>
      </div>
    )
  }
}

function StatCardPreview({ component, colors, style }) {
  const [val] = useState(() => {
    const t = (component.title || '').toLowerCase()
    if (t.includes('revenue')) return `$${(Math.random() * 50000 + 5000).toFixed(0)}`
    if (t.includes('growth')) return `+${(Math.random() * 30 + 5).toFixed(1)}%`
    if (t.includes('active')) return Math.floor(Math.random() * 500) + 50
    return Math.floor(Math.random() * 1000) + 100
  })
  const [change] = useState(() => (Math.random() * 15 + 2).toFixed(1))

  return (
    <div style={{ ...style, padding: 20, display: 'flex', flexDirection: 'column', gap: 4 }}>
      <div style={{ fontSize: 12, color: colors.text_secondary || '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        {component.title || 'Metric'}
      </div>
      <div style={{ fontSize: 28, fontWeight: 700, fontFamily: 'JetBrains Mono, monospace' }}>{val}</div>
      <div style={{ fontSize: 11, color: colors.success || '#22c55e' }}>↑ {change}% from last month</div>
    </div>
  )
}

function TablePreview({ component, database, colors }) {
  const columns = component.table_columns || [
    { key: 'id', label: 'ID' }, { key: 'name', label: 'Name' }, { key: 'status', label: 'Status' },
  ]
  const [mockRows] = useState(() => generateMockData(columns, 5))

  return (
    <div style={{ overflow: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
        <thead>
          <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
            {columns.map((col, i) => (
              <th key={i} style={{ textAlign: 'left', padding: '10px 14px', fontWeight: 600, color: colors.text_secondary || '#94a3b8', fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                {col.label || col.key}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {mockRows.map((row, ri) => (
            <tr key={ri} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
              {columns.map((col, ci) => (
                <td key={ci} style={{ padding: '10px 14px' }}>
                  {col.type === 'badge' ? (
                    <span style={{
                      padding: '2px 10px', borderRadius: 12, fontSize: 11, fontWeight: 500,
                      background: row[col.key] === 'active' ? 'rgba(34,197,94,0.15)' : 'rgba(99,102,241,0.15)',
                      color: row[col.key] === 'active' ? (colors.success || '#22c55e') : (colors.primary || '#6366f1'),
                    }}>{row[col.key]}</span>
                  ) : row[col.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function FormPreview({ component, colors }) {
  const fields = component.form_fields || [
    { name: 'name', label: 'Name', type: 'text' }, { name: 'email', label: 'Email', type: 'email' },
  ]
  const inp = {
    width: '100%', padding: '8px 12px', background: 'rgba(255,255,255,0.05)',
    border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: 'inherit', fontFamily: 'inherit', fontSize: 13, outline: 'none',
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      {fields.slice(0, 6).map((field, i) => (
        <div key={i}>
          <label style={{ display: 'block', fontSize: 12, fontWeight: 500, marginBottom: 4, color: colors.text_secondary }}>
            {field.label || field.name}
            {field.required && <span style={{ color: colors.error || '#ef4444' }}> *</span>}
          </label>
          {field.type === 'textarea' ? (
            <textarea style={{ ...inp, minHeight: 80, resize: 'vertical' }} placeholder={field.placeholder || `Enter ${field.label || field.name}`} />
          ) : field.type === 'select' ? (
            <select style={inp}>
              <option>Select {field.label || field.name}</option>
              {field.options?.map((opt, j) => <option key={j} value={opt.value || opt}>{opt.label || opt}</option>)}
            </select>
          ) : (
            <input type={field.type || 'text'} style={inp} placeholder={field.placeholder || `Enter ${field.label || field.name}`} />
          )}
        </div>
      ))}
      <button style={{
        padding: '10px 20px',
        background: `linear-gradient(135deg, ${colors.primary || '#6366f1'}, ${colors.secondary || '#8b5cf6'})`,
        border: 'none', borderRadius: 8, color: 'white', fontWeight: 600, fontSize: 13, cursor: 'pointer', marginTop: 4,
      }}>Submit</button>
    </div>
  )
}

function ChartPreview({ component, colors }) {
  const cfg = component.chart_config || { type: 'bar' }
  const bars = [65, 82, 45, 93, 70, 56, 78]
  const max = Math.max(...bars)

  if (cfg.type === 'pie' || cfg.type === 'doughnut') {
    return (
      <div style={{
        width: 160, height: 160, borderRadius: '50%', margin: '0 auto', position: 'relative',
        background: `conic-gradient(${colors.primary || '#6366f1'} 0% 35%, ${colors.secondary || '#8b5cf6'} 35% 60%, ${colors.accent || '#06b6d4'} 60% 80%, ${colors.success || '#22c55e'} 80% 100%)`,
      }}>
        {cfg.type === 'doughnut' && <div style={{ position: 'absolute', inset: 30, borderRadius: '50%', background: colors.surface || '#1e293b' }} />}
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', alignItems: 'flex-end', gap: 8, height: 120, padding: '0 8px' }}>
      {bars.map((val, i) => (
        <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
          <div style={{
            width: '100%', height: `${(val / max) * 100}%`,
            background: `linear-gradient(180deg, ${colors.primary || '#6366f1'}, ${colors.primary || '#6366f1'}66)`,
            borderRadius: '4px 4px 0 0', minHeight: 4,
          }} />
          <span style={{ fontSize: 10, color: colors.text_secondary || '#94a3b8' }}>
            {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][i]}
          </span>
        </div>
      ))}
    </div>
  )
}

function ListPreview({ component, colors }) {
  const icons = ['📋', '📊', '📈', '📌']
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      {[1, 2, 3, 4].map((n, i) => (
        <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 12px', borderRadius: 8, cursor: 'pointer' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ width: 32, height: 32, borderRadius: 8, background: `${colors.primary || '#6366f1'}20`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14 }}>
              {icons[i]}
            </div>
            <div>
              <div style={{ fontWeight: 500, fontSize: 13 }}>{component.title} Item {n}</div>
              <div style={{ fontSize: 11, color: colors.text_secondary }}>Updated 2h ago</div>
            </div>
          </div>
          <span style={{ color: colors.text_secondary, fontSize: 14 }}>›</span>
        </div>
      ))}
    </div>
  )
}
