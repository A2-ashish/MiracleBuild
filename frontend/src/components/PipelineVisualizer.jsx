export default function PipelineVisualizer({ stages }) {
  return (
    <div className="pipeline">
      {stages.map((stage) => (
        <div key={stage.id} className={`pipeline-stage ${stage.status}`}>
          <div className={`pipeline-stage-icon ${stage.status}`}>
            {stage.status === 'completed' ? '✓' :
             stage.status === 'error' ? '✗' :
             stage.status === 'running' ? '◉' :
             stage.icon}
          </div>
          <div className="pipeline-stage-content">
            <div className="pipeline-stage-title">{stage.name}</div>
            <div className="pipeline-stage-subtitle">
              {stage.status === 'error' && stage.errorMessage
                ? stage.errorMessage
                : stage.subtitle}
            </div>
            {stage.status === 'error' && stage.errorSuggestion && (
              <div className="pipeline-stage-error-suggestion">
                💡 {stage.errorSuggestion}
              </div>
            )}
            {(stage.duration || stage.tokens) && (
              <div className="pipeline-stage-meta">
                {stage.duration != null && (
                  <span className="pipeline-stage-meta-item">
                    ⏱ {(stage.duration / 1000).toFixed(1)}s
                  </span>
                )}
                {stage.tokens != null && (
                  <span className="pipeline-stage-meta-item">
                    🔤 {stage.tokens.toLocaleString()} tokens
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
