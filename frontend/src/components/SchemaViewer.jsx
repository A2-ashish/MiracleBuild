import { useState, useMemo } from 'react'

const SCHEMA_TABS = [
  { id: 'database', label: '🗃️ Database', path: 'database' },
  { id: 'api', label: '🔌 API', path: 'api' },
  { id: 'ui', label: '🎨 UI', path: 'ui' },
  { id: 'auth', label: '🔒 Auth', path: 'auth' },
  { id: 'business_logic', label: '📋 Logic', path: 'business_logic' },
]

function syntaxHighlight(json) {
  if (typeof json !== 'string') {
    json = JSON.stringify(json, null, 2)
  }
  json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  return json.replace(
    /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
    (match) => {
      let cls = 'json-number'
      if (/^"/.test(match)) {
        if (/:$/.test(match)) {
          cls = 'json-key'
          match = match.slice(0, -1) + ':'
        } else {
          cls = 'json-string'
        }
      } else if (/true|false/.test(match)) {
        cls = 'json-boolean'
      } else if (/null/.test(match)) {
        cls = 'json-null'
      }
      return `<span class="${cls}">${match}</span>`
    }
  )
}

export default function SchemaViewer({ config, fullView = false }) {
  const [activeTab, setActiveTab] = useState('database')
  const [copied, setCopied] = useState(false)

  const displayData = useMemo(() => {
    if (!config) return null
    if (fullView) return config
    return config[activeTab] || null
  }, [config, activeTab, fullView])

  const jsonString = useMemo(() => {
    if (!displayData) return ''
    return JSON.stringify(displayData, null, 2)
  }, [displayData])

  const highlightedJson = useMemo(() => {
    if (!jsonString) return ''
    return syntaxHighlight(jsonString)
  }, [jsonString])

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(jsonString)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (e) {
      console.error('Failed to copy:', e)
    }
  }

  if (!config) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">📐</div>
        <div className="empty-state-title">No schemas generated yet</div>
      </div>
    )
  }

  return (
    <div>
      {!fullView && (
        <div className="tabs" style={{ marginBottom: 'var(--space-4)' }}>
          {SCHEMA_TABS.map(tab => (
            <button
              key={tab.id}
              className={`tab ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>
      )}

      <div className="json-viewer">
        <button className="btn btn-sm btn-secondary json-copy-btn" onClick={handleCopy}>
          {copied ? '✓ Copied' : '📋 Copy'}
        </button>
        <pre dangerouslySetInnerHTML={{ __html: highlightedJson || '<span class="json-null">null</span>' }} />
      </div>

      {!fullView && displayData && (
        <div style={{ marginTop: 'var(--space-3)', display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
          {activeTab === 'database' && config.database?.tables && (
            <span className="badge badge-info">
              {config.database.tables.length} tables
            </span>
          )}
          {activeTab === 'api' && config.api?.endpoints && (
            <span className="badge badge-info">
              {config.api.endpoints.length} endpoints
            </span>
          )}
          {activeTab === 'ui' && config.ui?.pages && (
            <span className="badge badge-info">
              {config.ui.pages.length} pages
            </span>
          )}
          {activeTab === 'auth' && config.auth?.roles && (
            <span className="badge badge-info">
              {config.auth.roles.length} roles
            </span>
          )}
          {activeTab === 'business_logic' && config.business_logic?.rules && (
            <span className="badge badge-info">
              {config.business_logic.rules.length} rules
            </span>
          )}
        </div>
      )}
    </div>
  )
}
