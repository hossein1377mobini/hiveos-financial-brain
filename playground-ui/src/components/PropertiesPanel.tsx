import { useCallback, useState, useEffect } from 'react';
import type { PlaygroundNode } from '../types/workflow';

interface PropertiesPanelProps {
  node: PlaygroundNode | null;
  onUpdateNode: (nodeId: string, data: Partial<PlaygroundNode['data']>) => void;
  onDeleteNode: (nodeId: string) => void;
}

export function PropertiesPanel({ node, onUpdateNode, onDeleteNode }: PropertiesPanelProps) {
  const [localLabel, setLocalLabel] = useState('');
  const [localDescription, setLocalDescription] = useState('');
  const [localConfig, setLocalConfig] = useState('');

  useEffect(() => {
    if (node) {
      setLocalLabel(node.data.label || '');
      setLocalDescription(node.data.description || '');
      setLocalConfig(JSON.stringify(node.data.config || {}, null, 2));
    }
  }, [node]);

  const handleLabelChange = useCallback((value: string) => {
    setLocalLabel(value);
    if (node) {
      onUpdateNode(node.id, { label: value });
    }
  }, [node, onUpdateNode]);

  const handleDescriptionChange = useCallback((value: string) => {
    setLocalDescription(value);
    if (node) {
      onUpdateNode(node.id, { description: value });
    }
  }, [node, onUpdateNode]);

  const handleConfigChange = useCallback((value: string) => {
    setLocalConfig(value);
    try {
      const parsed = JSON.parse(value);
      if (node) {
        onUpdateNode(node.id, { config: parsed });
      }
    } catch {
      // Invalid JSON, don't update
    }
  }, [node, onUpdateNode]);

  if (!node) {
    return (
      <div
        style={{
          width: 280,
          background: 'var(--bg-panel)',
          borderLeft: '1px solid var(--border)',
          display: 'flex',
          flexDirection: 'column',
          flexShrink: 0,
        }}
      >
        <div
          style={{
            padding: '24px 16px',
            textAlign: 'center',
          }}
        >
          <div
            style={{
              fontSize: 32,
              marginBottom: 12,
              opacity: 0.3,
            }}
          >
            👈
          </div>
          <p
            style={{
              fontSize: 13,
              color: 'var(--text-tertiary)',
              fontFamily: 'Inter Variable, Inter, system-ui, sans-serif',
              lineHeight: 1.5,
              margin: 0,
            }}
          >
            Select a node to edit its properties
          </p>
        </div>
      </div>
    );
  }

  const category = node.data.category || 'action';
  const categoryColors: Record<string, string> = {
    trigger: '#10b981',
    action: '#7170ff',
    ai: '#f59e0b',
    flow: '#8a8f98',
  };
  const accentColor = categoryColors[category] || '#7170ff';

  return (
    <div
      style={{
        width: 280,
        background: 'var(--bg-panel)',
        borderLeft: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        flexShrink: 0,
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '16px',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 14 }}>{node.data.icon || '📦'}</span>
          <span
            style={{
              fontSize: 13,
              fontWeight: 510,
              color: 'var(--text-primary)',
              fontFamily: 'Inter Variable, Inter, system-ui, sans-serif',
            }}
          >
            Properties
          </span>
        </div>
        <button
          onClick={() => onDeleteNode(node.id)}
          style={{
            background: 'rgba(239,68,68,0.1)',
            border: '1px solid rgba(239,68,68,0.2)',
            borderRadius: 6,
            color: '#ef4444',
            padding: '4px 8px',
            fontSize: 11,
            fontWeight: 510,
            fontFamily: 'Inter Variable, Inter, system-ui, sans-serif',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
          }}
          onMouseEnter={e => {
            e.currentTarget.style.background = 'rgba(239,68,68,0.2)';
          }}
          onMouseLeave={e => {
            e.currentTarget.style.background = 'rgba(239,68,68,0.1)';
          }}
        >
          Delete
        </button>
      </div>

      {/* Properties Form */}
      <div
        style={{
          flex: 1,
          overflow: 'auto',
          padding: '16px',
          display: 'flex',
          flexDirection: 'column',
          gap: 16,
        }}
      >
        {/* Node Type Badge */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
          }}
        >
          <div
            style={{
              width: 6,
              height: 6,
              borderRadius: '50%',
              background: accentColor,
            }}
          />
          <span
            style={{
              fontSize: 11,
              fontWeight: 510,
              color: accentColor,
              fontFamily: 'Inter Variable, Inter, system-ui, sans-serif',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
            }}
          >
            {category} node
          </span>
          <span
            style={{
              fontSize: 10,
              color: 'var(--text-quaternary)',
              fontFamily: 'var(--font-mono)',
              marginLeft: 'auto',
            }}
          >
            {node.type}
          </span>
        </div>

        {/* Label */}
        <Field label="Label">
          <input
            value={localLabel}
            onChange={e => handleLabelChange(e.target.value)}
            placeholder="Node name"
            style={inputStyle}
          />
        </Field>

        {/* Description */}
        <Field label="Description">
          <textarea
            value={localDescription}
            onChange={e => handleDescriptionChange(e.target.value)}
            placeholder="What does this node do?"
            rows={2}
            style={{ ...inputStyle, resize: 'vertical', minHeight: 40 }}
          />
        </Field>

        {/* Config JSON */}
        <Field label="Configuration (JSON)">
          <textarea
            value={localConfig}
            onChange={e => handleConfigChange(e.target.value)}
            rows={8}
            style={{
              ...inputStyle,
              fontFamily: 'var(--font-mono)',
              fontSize: 11,
              resize: 'vertical',
              minHeight: 120,
              tabSize: 2,
            }}
          />
        </Field>

        {/* Execution Info */}
        {node.data.executionStatus && node.data.executionStatus !== 'idle' && (
          <div
            style={{
              padding: '10px 12px',
              background: 'rgba(255,255,255,0.03)',
              borderRadius: 8,
              border: '1px solid var(--border-subtle)',
            }}
          >
            <div
              style={{
                fontSize: 11,
                fontWeight: 510,
                color: 'var(--text-secondary)',
                fontFamily: 'Inter Variable, Inter, system-ui, sans-serif',
                marginBottom: 8,
              }}
            >
              Execution
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <InfoRow label="Status" value={node.data.executionStatus} />
              {node.data.executionDuration !== undefined && (
                <InfoRow label="Duration" value={`${node.data.executionDuration}ms`} />
              )}
              {node.data.executionError && (
                <InfoRow label="Error" value={node.data.executionError} />
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/* ─── Sub-components ─── */

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      <label
        style={{
          fontSize: 11,
          fontWeight: 510,
          color: 'var(--text-secondary)',
          fontFamily: 'Inter Variable, Inter, system-ui, sans-serif',
        }}
      >
        {label}
      </label>
      {children}
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  const valueColor = value === 'error' ? '#ef4444' : value === 'running' ? '#7170ff' : 'var(--text-tertiary)';
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <span style={{ fontSize: 11, color: 'var(--text-quaternary)', fontFamily: 'var(--font-sans)' }}>
        {label}
      </span>
      <span style={{ fontSize: 11, color: valueColor, fontFamily: 'var(--font-mono)' }}>
        {value}
      </span>
    </div>
  );
}

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '8px 10px',
  background: 'rgba(255,255,255,0.02)',
  border: '1px solid var(--border)',
  borderRadius: 6,
  color: 'var(--text-primary)',
  fontSize: 12,
  fontFamily: 'Inter Variable, Inter, system-ui, sans-serif',
  outline: 'none',
  transition: 'border-color 0.15s ease',
};
