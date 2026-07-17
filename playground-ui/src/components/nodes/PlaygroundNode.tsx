import { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import type { PlaygroundNodeData } from '../../types/workflow';

const NODE_COLORS: Record<string, { bg: string; border: string; text: string; accent: string }> = {
  trigger: { bg: 'rgba(16,185,129,0.12)', border: 'rgba(16,185,129,0.4)', text: '#10b981', accent: '#10b981' },
  action:  { bg: 'rgba(113,112,255,0.12)', border: 'rgba(113,112,255,0.4)', text: '#7170ff', accent: '#7170ff' },
  ai:      { bg: 'rgba(245,158,11,0.12)', border: 'rgba(245,158,11,0.4)', text: '#f59e0b', accent: '#f59e0b' },
  flow:    { bg: 'rgba(138,143,152,0.12)', border: 'rgba(138,143,152,0.4)', text: '#8a8f98', accent: '#8a8f98' },
};

const EXECUTION_COLORS: Record<string, string> = {
  idle: 'transparent',
  running: '#7170ff',
  completed: '#10b981',
  error: '#ef4444',
  skipped: '#62666d',
};

function BaseNode({ data, selected }: NodeProps<PlaygroundNodeData>) {
  const cat = data.category || 'action';
  const colors = NODE_COLORS[cat] || NODE_COLORS.action;
  const execColor = EXECUTION_COLORS[data.executionStatus || 'idle'];
  const isRunning = data.executionStatus === 'running';

  return (
    <div
      style={{
        background: colors.bg,
        border: `1px solid ${selected ? colors.accent : colors.border}`,
        borderRadius: '10px',
        padding: '12px 16px',
        minWidth: 180,
        maxWidth: 240,
        backdropFilter: 'blur(8px)',
        boxShadow: selected
          ? `0 0 0 1px ${colors.accent}, 0 4px 20px rgba(0,0,0,0.3)`
          : '0 2px 8px rgba(0,0,0,0.2)',
        transition: 'all 0.15s ease',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Execution status indicator bar */}
      {data.executionStatus && data.executionStatus !== 'idle' && (
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 3,
            background: execColor,
            borderRadius: '10px 10px 0 0',
          }}
        />
      )}

      {/* Running animation */}
      {isRunning && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            borderRadius: 10,
            background: 'linear-gradient(90deg, transparent, rgba(113,112,255,0.08), transparent)',
            animation: 'shimmer 1.5s ease-in-out infinite',
            pointerEvents: 'none',
          }}
        />
      )}

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
        <span style={{ fontSize: 16 }}>{data.icon || '📦'}</span>
        <span
          style={{
            fontFamily: 'Inter Variable, Inter, system-ui, sans-serif',
            fontSize: 13,
            fontWeight: 510,
            color: colors.text,
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
        >
          {data.label}
        </span>
        {data.executionDuration !== undefined && data.executionStatus === 'completed' && (
          <span
            style={{
              fontSize: 10,
              color: 'var(--text-quaternary)',
              marginLeft: 'auto',
              fontFamily: 'var(--font-mono)',
            }}
          >
            {data.executionDuration}ms
          </span>
        )}
      </div>

      {/* Description */}
      {data.description && (
        <p
          style={{
            fontSize: 11,
            color: 'var(--text-tertiary)',
            fontFamily: 'Inter Variable, Inter, system-ui, sans-serif',
            lineHeight: 1.4,
            margin: 0,
          }}
        >
          {data.description}
        </p>
      )}

      {/* Config preview */}
      {data.config && Object.keys(data.config).length > 0 && (
        <div
          style={{
            marginTop: 8,
            padding: '6px 8px',
            background: 'rgba(0,0,0,0.2)',
            borderRadius: 6,
            fontSize: 11,
            fontFamily: 'var(--font-mono)',
            color: 'var(--text-quaternary)',
            maxHeight: 60,
            overflow: 'hidden',
          }}
        >
          {Object.entries(data.config).slice(0, 2).map(([key, val]) => (
            <div key={key} style={{ lineHeight: 1.4 }}>
              <span style={{ color: 'var(--text-tertiary)' }}>{key}:</span>{' '}
              <span>{String(val).slice(0, 40)}</span>
            </div>
          ))}
          {Object.keys(data.config).length > 2 && (
            <div style={{ color: 'var(--text-quaternary)' }}>
              +{Object.keys(data.config).length - 2} more
            </div>
          )}
        </div>
      )}

      {/* Error display */}
      {data.executionError && (
        <div
          style={{
            marginTop: 8,
            padding: '4px 8px',
            background: 'rgba(239,68,68,0.1)',
            borderRadius: 4,
            fontSize: 11,
            fontFamily: 'var(--font-mono)',
            color: '#ef4444',
            wordBreak: 'break-all',
            maxHeight: 40,
            overflow: 'hidden',
          }}
        >
          {data.executionError}
        </div>
      )}

      {/* Handles */}
      <Handle
        type="target"
        position={Position.Left}
        style={{
          width: 8,
          height: 8,
          background: 'var(--text-quaternary)',
          border: '2px solid var(--bg-deep)',
        }}
      />
      <Handle
        type="source"
        position={Position.Right}
        style={{
          width: 8,
          height: 8,
          background: colors.accent,
          border: '2px solid var(--bg-deep)',
        }}
      />
    </div>
  );
}

export const TriggerNode = memo(BaseNode);
export const ActionNode = memo(BaseNode);
export const AiNode = memo(BaseNode);
export const FlowNode = memo(BaseNode);
export const PlaygroundNode = memo(BaseNode);

/* ─── Shimmer Keyframes ─── */
if (typeof document !== 'undefined') {
  const style = document.createElement('style');
  style.textContent = `
    @keyframes shimmer {
      0% { opacity: 0; }
      50% { opacity: 1; }
      100% { opacity: 0; }
    }
  `;
  document.head.appendChild(style);
}
