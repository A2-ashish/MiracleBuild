import { useState, useCallback } from 'react'
import './index.css'
import PromptInput from './components/PromptInput'
import PipelineVisualizer from './components/PipelineVisualizer'
import SchemaViewer from './components/SchemaViewer'
import ValidationReport from './components/ValidationReport'
import MetricsPanel from './components/MetricsPanel'
import RuntimePreview from './components/RuntimePreview'

const API_BASE = import.meta.env.VITE_API_URL || ''

const INITIAL_STAGES = [
  { id: 'intent', name: 'Intent Extraction', icon: '🔍', subtitle: 'Parsing entities, features, roles', status: 'pending' },
  { id: 'design', name: 'System Design', icon: '🏗️', subtitle: 'Architecture & relationships', status: 'pending' },
  { id: 'schemas', name: 'Schema Generation', icon: '⚙️', subtitle: 'DB, API, UI, Auth, Logic', status: 'pending' },
  { id: 'refinement', name: 'Refinement', icon: '🔧', subtitle: 'Cross-layer consistency', status: 'pending' },
  { id: 'validation', name: 'Validation & Repair', icon: '✅', subtitle: '12 checks + auto-repair', status: 'pending' },
]

function App() {
  const [stages, setStages] = useState(INITIAL_STAGES)
  const [result, setResult] = useState(null)
  const [isCompiling, setIsCompiling] = useState(false)
  const [error, setError] = useState(null)
  const [selectedModel, setSelectedModel] = useState('gemini-2.5-pro')
  const [activeOutputTab, setActiveOutputTab] = useState('pipeline')

  const updateStage = useCallback((stageId, updates) => {
    setStages(prev => prev.map(s => s.id === stageId ? { ...s, ...updates } : s))
  }, [])

  const handleCompile = useCallback(async (prompt) => {
    setIsCompiling(true)
    setError(null)
    setResult(null)
    setStages(INITIAL_STAGES)
    setActiveOutputTab('pipeline')

    try {
      // Use SSE for streaming stage updates
      const params = new URLSearchParams({ prompt, model: selectedModel })
      const eventSource = new EventSource(`${API_BASE}/api/compile/stream?${params}`)

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)

          if (data.type === 'stage_update') {
            updateStage(data.stage, {
              status: data.status,
              duration: data.duration_ms,
              tokens: data.tokens,
            })
          } else if (data.type === 'complete') {
            setResult(data.result)
            setIsCompiling(false)
            setActiveOutputTab('schemas')
            eventSource.close()
          } else if (data.type === 'error') {
            setError(data.message)
            setIsCompiling(false)
            eventSource.close()
          }
        } catch (e) {
          console.error('Failed to parse SSE event:', e)
        }
      }

      eventSource.onerror = (e) => {
        console.error('SSE error:', e)
        // Fallback to regular POST
        eventSource.close()
        fallbackCompile(prompt)
      }
    } catch (err) {
      fallbackCompile(prompt)
    }
  }, [selectedModel, updateStage])

  const fallbackCompile = async (prompt) => {
    try {
      // Update stages to show progress
      const stageOrder = ['intent', 'design', 'schemas', 'refinement', 'validation']

      for (const stage of stageOrder) {
        updateStage(stage, { status: 'running' })
        await new Promise(r => setTimeout(r, 300))
      }

      const response = await fetch(`${API_BASE}/api/compile`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, model: selectedModel }),
      })

      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: 'Compilation failed' }))
        throw new Error(err.detail || 'Compilation failed')
      }

      const data = await response.json()

      // Update all stages based on result
      for (const stage of stageOrder) {
        const duration = data.metrics?.stage_durations?.[stage]
        const tokens = data.metrics?.tokens_per_stage?.[stage]
        updateStage(stage, {
          status: data.success ? 'completed' : 'error',
          duration,
          tokens,
        })
      }

      setResult(data)
      setActiveOutputTab('schemas')
    } catch (err) {
      setError(err.message)
      setStages(prev => prev.map(s => ({
        ...s,
        status: s.status === 'running' ? 'error' : s.status
      })))
    } finally {
      setIsCompiling(false)
    }
  }

  return (
    <div className="app">
      <div className="animated-bg">
        <div className="orb orb-1"></div>
        <div className="orb orb-2"></div>
        <div className="orb orb-3"></div>
      </div>
      <header className="app-header">
        <div className="app-logo">
          <div className="app-logo-icon">⚡</div>
          <span className="app-logo-text">Miracle Build</span>
          <span className="app-logo-badge">Compiler</span>
        </div>
        <div className="app-header-actions">
          <div className="model-selector">
            <span className="model-selector-label">Model:</span>
            <select
              className="select"
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              disabled={isCompiling}
            >
              <option value="gemini-2.5-pro">Gemini 2.5 Pro</option>
              <option value="gemini-2.5-flash">Gemini 2.5 Flash</option>
              <option value="gemini-2.0-flash">Gemini 2.0 Flash</option>
            </select>
          </div>
        </div>
      </header>

      <main className="app-main">
        {/* Left Panel — Input */}
        <div className="prompt-section animate-fade-in">
          <PromptInput
            onCompile={handleCompile}
            isCompiling={isCompiling}
          />

          <div className="glass-card">
            <div className="glass-card-header">
              <h2 className="glass-card-title">⚙️ Pipeline</h2>
              {result && (
                <span className={`badge ${result.success ? 'badge-success' : 'badge-error'}`}>
                  {result.success ? '✓ Success' : '✗ Failed'}
                </span>
              )}
            </div>
            <div className="glass-card-body">
              <PipelineVisualizer stages={stages} />
            </div>
          </div>

          {result?.metrics && (
            <div className="glass-card animate-fade-in">
              <div className="glass-card-header">
                <h2 className="glass-card-title">📊 Metrics</h2>
              </div>
              <div className="glass-card-body">
                <MetricsPanel metrics={result.metrics} />
              </div>
            </div>
          )}
        </div>

        {/* Right Panel — Output */}
        <div className="animate-fade-in" style={{ animationDelay: '0.1s' }}>
          {error && (
            <div className="glass-card" style={{ marginBottom: 'var(--space-5)', borderColor: 'var(--color-error)' }}>
              <div className="glass-card-body" style={{ color: 'var(--color-error)' }}>
                <strong>⚠ Compilation Error:</strong> {error}
              </div>
            </div>
          )}

          {!result && !isCompiling && !error && (
            <div className="glass-card">
              <div className="glass-card-body">
                <div className="empty-state">
                  <div className="empty-state-icon">🏭</div>
                  <div className="empty-state-title">Ready to Compile</div>
                  <div className="empty-state-text">
                    Enter a natural language description of your application and hit Compile.
                    The pipeline will generate validated, executable configuration.
                  </div>
                </div>
              </div>
            </div>
          )}

          {isCompiling && !result && (
            <div className="glass-card">
              <div className="glass-card-body">
                <div className="empty-state">
                  <div className="empty-state-icon" style={{ animation: 'spin 2s linear infinite' }}>⚙️</div>
                  <div className="empty-state-title">Compiling...</div>
                  <div className="empty-state-text">
                    The multi-stage pipeline is processing your prompt.
                    Watch the pipeline stages on the left for real-time progress.
                  </div>
                </div>
              </div>
            </div>
          )}

          {result && (
            <>
              <div className="glass-card" style={{ marginBottom: 'var(--space-5)' }}>
                <div className="glass-card-header">
                  <div className="tabs">
                    {[
                      { id: 'schemas', label: '📐 Schemas' },
                      { id: 'validation', label: '✅ Validation' },
                      { id: 'runtime', label: '🚀 Preview' },
                      { id: 'full', label: '📄 Full Config' },
                    ].map(tab => (
                      <button
                        key={tab.id}
                        className={`tab ${activeOutputTab === tab.id ? 'active' : ''}`}
                        onClick={() => setActiveOutputTab(tab.id)}
                      >
                        {tab.label}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="glass-card-body">
                  {activeOutputTab === 'schemas' && (
                    <SchemaViewer config={result.config} />
                  )}
                  {activeOutputTab === 'validation' && (
                    <ValidationReport report={result.validation_report} />
                  )}
                  {activeOutputTab === 'runtime' && (
                    <RuntimePreview config={result.config} />
                  )}
                  {activeOutputTab === 'full' && (
                    <SchemaViewer config={result.config} fullView />
                  )}
                </div>
              </div>

              {result.assumptions?.length > 0 && (
                <div className="glass-card animate-fade-in">
                  <div className="glass-card-header">
                    <h2 className="glass-card-title">💡 Assumptions Made</h2>
                  </div>
                  <div className="glass-card-body">
                    <ul style={{ paddingLeft: 'var(--space-5)', color: 'var(--color-text-secondary)', fontSize: 'var(--text-sm)' }}>
                      {result.assumptions.map((a, i) => (
                        <li key={i} style={{ marginBottom: 'var(--space-2)' }}>{a}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </main>
    </div>
  )
}

export default App
