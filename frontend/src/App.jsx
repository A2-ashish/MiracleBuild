import { useState, useCallback, useEffect } from 'react'
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
  const [errorDetails, setErrorDetails] = useState(null)
  const [selectedModel, setSelectedModel] = useState('gemini-2.5-pro')
  const [theme, setTheme] = useState('liquid')
  const [activeOutputTab, setActiveOutputTab] = useState('pipeline')
  const [lastPrompt, setLastPrompt] = useState('')

  const updateStage = useCallback((stageId, updates) => {
    setStages(prev => prev.map(s => s.id === stageId ? { ...s, ...updates } : s))
  }, [])

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  // Map backend stage names to frontend stage IDs
  const mapStageName = useCallback((backendName) => {
    const STAGE_NAME_MAP = {
      'intent_extraction': 'intent',
      'system_design': 'design',
      'schema_generation': 'schemas',
      'refinement': 'refinement',
      'validation': 'validation',
    }
    return STAGE_NAME_MAP[backendName] || backendName
  }, [])

  const handleCompile = useCallback(async (prompt) => {
    setIsCompiling(true)
    setError(null)
    setErrorDetails(null)
    setResult(null)
    setStages(INITIAL_STAGES)
    setActiveOutputTab('pipeline')
    setLastPrompt(prompt)

    try {
      // Use SSE for streaming stage updates
      const params = new URLSearchParams({ prompt, model: selectedModel })
      const eventSource = new EventSource(`${API_BASE}/api/compile/stream?${params}`)

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)

          if (data.type === 'stage_update') {
            const stageUpdate = {
              status: data.status,
              duration: data.duration_ms,
              tokens: data.tokens,
            }
            // Attach error details to the specific stage that failed
            if (data.status === 'error' && data.error_message) {
              stageUpdate.errorMessage = data.error_message
              stageUpdate.errorSuggestion = data.error_suggestion
              stageUpdate.errorCode = data.error_code
            }
            updateStage(mapStageName(data.stage), stageUpdate)
          } else if (data.type === 'complete') {
            setResult(data.result)
            setIsCompiling(false)
            setActiveOutputTab('schemas')
            eventSource.close()
          } else if (data.type === 'error') {
            setError(data.message || 'Compilation failed')
            setErrorDetails({
              code: data.error_code,
              message: data.message,
              suggestion: data.error_suggestion,
              failedStage: data.failed_stage,
              retryable: data.retryable,
              errors: data.errors,
            })
            if (data.result) {
              setResult(data.result)
            }
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
  }, [selectedModel, updateStage, mapStageName])

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

      // Backend uses different stage names than frontend IDs
      const stageToBackend = {
        'intent': 'intent_extraction',
        'design': 'system_design',
        'schemas': 'schema_generation',
        'refinement': 'refinement',
        'validation': 'validation',
      }

      // Update all stages based on result
      for (const stage of stageOrder) {
        const backendName = stageToBackend[stage] || stage
        const duration = data.metrics?.stage_durations?.[backendName] || data.metrics?.stage_durations?.[stage]
        const tokens = data.metrics?.tokens_per_stage?.[backendName] || data.metrics?.tokens_per_stage?.[stage]

        // If this is the failed stage, mark it as error; previous stages as completed
        const failedBackendStage = data.failed_stage
        const failedFrontendStage = Object.entries(stageToBackend).find(([, v]) => v === failedBackendStage)?.[0]
        let status = data.success ? 'completed' : 'error'
        if (!data.success && failedFrontendStage) {
          const stageIdx = stageOrder.indexOf(stage)
          const failedIdx = stageOrder.indexOf(failedFrontendStage)
          if (stageIdx < failedIdx) status = 'completed'
          else if (stageIdx > failedIdx) status = 'pending'
          else status = 'error'
        }

        updateStage(stage, { status, duration, tokens })
      }

      if (!data.success && data.error_message) {
        setError(data.error_message)
        setErrorDetails({
          code: data.error_code,
          message: data.error_message,
          suggestion: data.error_suggestion,
          failedStage: data.failed_stage,
          retryable: data.retryable,
          errors: data.errors,
        })
      }

      setResult(data)
      setActiveOutputTab('schemas')
    } catch (err) {
      setError(err.message)
      setErrorDetails({
        code: 'NETWORK_ERROR',
        message: err.message,
        suggestion: 'Check your network connection and ensure the backend server is running.',
        retryable: true,
      })
      setStages(prev => prev.map(s => ({
        ...s,
        status: s.status === 'running' ? 'error' : s.status
      })))
    } finally {
      setIsCompiling(false)
    }
  }

  return (
    <>
      <div className="liquid-bg">
        {theme === 'liquid' && (
          <>
            <div className="blob blob-1"></div>
            <div className="blob blob-2"></div>
            <div className="blob blob-3"></div>
          </>
        )}
      </div>
      <div className="app">
        <header className="app-header">
        <div className="app-logo">
          <div className="app-logo-icon">⚡</div>
          <span className="app-logo-text">Miracle Build</span>
          <span className="app-logo-badge">Compiler</span>
        </div>
        <div className="app-header-actions">
          <div className="model-selector">
            <span className="model-selector-label" style={{ marginRight: '8px', fontSize: '14px', fontWeight: '500' }}>Theme:</span>
            <select
              className="select"
              value={theme}
              onChange={(e) => setTheme(e.target.value)}
              style={{ marginRight: '16px' }}
            >
              <option value="liquid">Liquid</option>
              <option value="light">Light</option>
            </select>
          </div>
          <div className="model-selector">
            <span className="model-selector-label" style={{ marginRight: '8px', fontSize: '14px', fontWeight: '500' }}>Model:</span>
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
            <div className="glass-card error-card" style={{ marginBottom: 'var(--space-5)', borderColor: 'var(--color-error)' }}>
              <div className="glass-card-body">
                <div className="error-header">
                  <div className="error-icon">⚠</div>
                  <div className="error-title-section">
                    <strong className="error-title">Compilation Failed</strong>
                    {errorDetails?.code && (
                      <span className="error-code-badge">{errorDetails.code.replace(/_/g, ' ')}</span>
                    )}
                  </div>
                </div>
                <div className="error-message">{error}</div>
                {errorDetails?.suggestion && (
                  <div className="error-suggestion">
                    <span className="error-suggestion-icon">💡</span>
                    <span>{errorDetails.suggestion}</span>
                  </div>
                )}
                {errorDetails?.failedStage && (
                  <div className="error-stage-info">
                    Failed at: <strong>{errorDetails.failedStage.replace(/_/g, ' ')}</strong>
                  </div>
                )}
                {errorDetails?.retryable && lastPrompt && (
                  <button
                    className="btn btn-primary btn-retry"
                    onClick={() => handleCompile(lastPrompt)}
                    disabled={isCompiling}
                  >
                    🔄 Retry Compilation
                  </button>
                )}
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
  </>
  )
}

export default App
