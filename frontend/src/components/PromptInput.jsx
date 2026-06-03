import { useState, useRef, useEffect } from 'react'

const EXAMPLE_PROMPTS = [
  'Build a CRM with login, contacts, dashboard, role-based access, and premium plan with payments.',
  'Create a project management tool with Kanban boards, team assignments, and deadlines.',
  'Build an e-commerce store with product catalog, shopping cart, checkout, and order tracking.',
  'Build a restaurant reservation system with table management and menu builder.',
  'Create a healthcare appointment booking system with doctor profiles and patient records.',
]

export default function PromptInput({ onCompile, isCompiling }) {
  const [prompt, setPrompt] = useState('')
  const [isRecording, setIsRecording] = useState(false)
  const recognitionRef = useRef(null)

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = false; // Only get final results to avoid weird overlapping state updates
      
      recognition.onstart = () => setIsRecording(true);
      
      recognition.onresult = (event) => {
        for (let i = event.resultIndex; i < event.results.length; i++) {
          if (event.results[i].isFinal) {
            const transcript = event.results[i][0].transcript;
            setPrompt((prev) => {
              const spacer = prev && !prev.endsWith(' ') ? ' ' : '';
              return prev + spacer + transcript;
            });
          }
        }
      };
      
      recognition.onerror = (event) => {
        console.error('Speech recognition error', event.error);
        setIsRecording(false);
      };
      
      recognition.onend = () => {
        setIsRecording(false);
      };
      
      recognitionRef.current = recognition;
    }
  }, []);

  const toggleRecording = () => {
    if (isRecording) {
      recognitionRef.current?.stop();
    } else {
      recognitionRef.current?.start();
    }
  };

  const handleSubmit = () => {
    if (prompt.trim() && !isCompiling) {
      if (isRecording) recognitionRef.current?.stop();
      onCompile(prompt.trim())
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      handleSubmit()
    }
  }

  return (
    <div className="glass-card">
      <div className="glass-card-header">
        <h2 className="glass-card-title">📝 Application Prompt</h2>
        <span className="prompt-char-count">{prompt.length} chars</span>
      </div>
      <div className="glass-card-body">
        <div className="prompt-textarea-wrapper">
          <textarea
            className="prompt-textarea"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Describe the application you want to build...&#10;&#10;Example: Build a CRM with login, contacts, dashboard, role-based access, and premium plan with payments. Admins can see analytics."
            disabled={isCompiling}
          />
          <div className="prompt-glow" />
        </div>

        <div className="prompt-footer" style={{ marginTop: 'var(--space-4)' }}>
          <div className="prompt-examples">
            {EXAMPLE_PROMPTS.map((ex, i) => (
              <button
                key={i}
                className="prompt-example-chip"
                onClick={() => setPrompt(ex)}
                disabled={isCompiling}
                title={ex}
              >
                {ex.substring(0, 40)}...
              </button>
            ))}
          </div>
        </div>

        <div style={{ marginTop: 'var(--space-4)', display: 'flex', gap: 'var(--space-3)', alignItems: 'center' }}>
          <button
            className={`btn btn-primary btn-lg ${isCompiling ? 'btn-loading' : ''}`}
            onClick={handleSubmit}
            disabled={!prompt.trim() || isCompiling}
            style={{ flex: 1 }}
          >
            <span className="btn-text">
              {isCompiling ? 'Compiling...' : '⚡ Compile Application'}
            </span>
          </button>
          
          {recognitionRef.current && (
            <button
              className={`btn btn-icon ${isRecording ? 'btn-record active' : 'btn-ghost'}`}
              onClick={toggleRecording}
              disabled={isCompiling}
              title={isRecording ? 'Stop Recording' : 'Start Voice Input'}
            >
              🎤
            </button>
          )}

          {prompt && (
            <button
              className="btn btn-ghost btn-icon"
              onClick={() => setPrompt('')}
              disabled={isCompiling}
              title="Clear"
            >
              ✕
            </button>
          )}
        </div>
        <div style={{ marginTop: 'var(--space-2)', fontSize: 'var(--text-xs)', color: 'var(--color-text-tertiary)', textAlign: 'center' }}>
          Press Ctrl+Enter to compile
        </div>
      </div>
    </div>
  )
}
