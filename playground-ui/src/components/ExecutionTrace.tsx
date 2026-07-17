import { useRef, useEffect } from 'react';
import type { ExecutionLogEntry } from '../types/workflow';

interface ExecutionTraceProps {
  logs: ExecutionLogEntry[];
  isRunning: boolean;
  onClear: () => void;
}

export function ExecutionTrace({ logs, isRunning, onClear }: ExecutionTraceProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const eventIcons: Record<string, string> = {
    start: '▶️',
    complete: '✅',
    error: '❌',
    step: '📌',
  };

  return (
    <div
      style={{
        height: 240,
        background: 'var(--bg-panel)',
        borderTop: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        flexShrink: 0,
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '8px 16px',
          borderBottom: '1px solid var(--border-subtle)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span
            style={{
              fontSize: 12,
              fontWeight: 510,
              color: 'var(--text-primary)',
              fontFamily: 'Inter Variable, Inter, system-ui, sans-serif',
            }}
          >
            Execution Trace
          </span>
          {isRunning && (
            <span
              style={{
                fontSize: 10,
                color: '#7170ff',
                fontFamily: 'var(--font-mono)',
                animation: 'pulse 1.5s ease-in-out infinite',
              }}
            >
              ● Running
            </span>
          )}
          <span
            style={{
              fontSize: 10,
              color: 'var(--text-quaternary)',
              fontFamily: 'var(--font-mono)',
            }}
          >
            {logs.length} events
          </span>
        </div>
        {logs.length > 0 && (
          <button
            onClick={onClear}
            style={{
              background: 'transparent',
              border: '1px solid var(--border)',
              borderRadius: 6,
              color: 'var(--text-tertiary)',
              padding: '3px 8px',
              fontSize: 10,
              fontFamily: 'Inter Variable, Inter, system-ui, sans-serif',
              cursor: 'pointer',
            }}
          >
            Clear
          </button>
        )}
      </div>

      {/* Log List */}
      <div
        style={{
          flex: 1,
          overflow: 'auto',
          padding: '4px 0',
          fontFamily: 'var(--font-mono)',
          fontSize: 11,
        }}
      >
        {logs.length === 0 && (
          <div
            style={{
              padding: '24px 16px',
              textAlign: 'center',
              color: 'var(--text-quaternary)',
              fontFamily: 'var(--font-sans)',
              fontSize: 12,
              lineHeight: 1.5,
            }}
          >
            {isRunning ? (
              <span>Waiting for execution events...</span>
            ) : (
              <span>
                No execution trace yet.<br />
                Run the flow to see real-time progress here.
              </span>
            )}
          </div>
        )}

        {logs.map(log => (
          <div
            key={log.id}
            style={{
              padding: '4px 16px',
              display: 'flex',
              gap: 8,
              alignItems: 'flex-start',
              borderLeft: '3px solid transparent',
              borderLeftColor:
                log.event === 'error' ? '#ef4444' :
                log.event === 'complete' ? '#10b981' :
                log.event === 'start' ? '#7170ff' :
                'transparent',
              background:
                log.event === 'error' ? 'rgba(239,68,68,0.04)' :
                log.event === 'start' ? 'rgba(113,112,255,0.04)' :
                'transparent',
            }}
          >
            {/* Timestamp */}
            <span
              style={{
                color: 'var(--text-quaternary)',
                whiteSpace: 'nowrap',
                fontSize: 10,
                minWidth: 65,
              }}
            >
              {formatTime(log.timestamp)}
            </span>

            {/* Icon */}
            <span style={{ fontSize: 10, width: 14, textAlign: 'center' }}>
              {eventIcons[log.event] || '•'}
            </span>

            {/* Node label + message */}
            <div style={{ flex: 1, minWidth: 0 }}>
              <span
                style={{
                  color: 'var(--text-secondary)',
                  fontWeight: 400,
                }}
              >
                {log.nodeLabel}
              </span>
              <span
                style={{
                  color: 'var(--text-tertiary)',
                  marginLeft: 4,
                }}
              >
                {log.message}
              </span>
              {log.duration !== undefined && (
                <span
                  style={{
                    color: 'var(--text-quaternary)',
                    marginLeft: 4,
                    fontSize: 10,
                  }}
                >
                  ({log.duration}ms)
                </span>
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}

function formatTime(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString('en-US', {
      minute: '2-digit',
      second: '2-digit',
      fractionalSecondDigits: 3,
    });
  } catch {
    return '--:--';
  }
}

/* ─── Pulse Animation ─── */
if (typeof document !== 'undefined') {
  const style = document.createElement('style');
  style.textContent = `
    @keyframes pulse {
      0%, 100% { opacity: 0.4; }
      50% { opacity: 1; }
    }
  `;
  if (!document.getElementById('trace-styles')) {
    style.id = 'trace-styles';
    document.head.appendChild(style);
  }
}
