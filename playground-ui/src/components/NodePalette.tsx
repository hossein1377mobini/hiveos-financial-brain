import { useCallback, useState } from 'react';
import { PALETTE_NODES, CATEGORIES } from '../api/playground';
import type { PaletteNodeType, NodeCategory } from '../types/workflow';

const NODE_COLORS: Record<string, string> = {
  trigger: '#10b981',
  action: '#7170ff',
  ai: '#f59e0b',
  flow: '#8a8f98',
};

interface NodePaletteProps {
  onDragStart: (nodeType: PaletteNodeType, event: React.DragEvent) => void;
}

export function NodePalette({ onDragStart }: NodePaletteProps) {
  const [activeCategory, setActiveCategory] = useState<NodeCategory>('trigger');

  const filteredNodes = PALETTE_NODES.filter(n => n.category === activeCategory);

  return (
    <div
      style={{
        width: 260,
        background: 'var(--bg-panel)',
        borderRight: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        flexShrink: 0,
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '16px 16px 12px',
          borderBottom: '1px solid var(--border-subtle)',
        }}
      >
        <h2
          style={{
            fontSize: 13,
            fontWeight: 510,
            color: 'var(--text-primary)',
            fontFamily: 'Inter Variable, Inter, system-ui, sans-serif',
            letterSpacing: '-0.13px',
            margin: 0,
          }}
        >
          Node Palette
        </h2>
        <p
          style={{
            fontSize: 11,
            color: 'var(--text-quaternary)',
            fontFamily: 'Inter Variable, Inter, system-ui, sans-serif',
            margin: '4px 0 0',
          }}
        >
          Drag nodes onto the canvas
        </p>
      </div>

      {/* Category Tabs */}
      <div
        style={{
          display: 'flex',
          gap: 0,
          padding: '4px 8px',
          borderBottom: '1px solid var(--border-subtle)',
          overflow: 'auto',
        }}
      >
        {CATEGORIES.map(cat => (
          <button
            key={cat.id}
            onClick={() => setActiveCategory(cat.id)}
            style={{
              flex: 1,
              padding: '6px 4px',
              background: activeCategory === cat.id ? 'var(--bg-surface)' : 'transparent',
              border: 'none',
              borderRadius: 6,
              color: activeCategory === cat.id ? 'var(--text-primary)' : 'var(--text-tertiary)',
              fontSize: 11,
              fontWeight: activeCategory === cat.id ? 510 : 400,
              fontFamily: 'Inter Variable, Inter, system-ui, sans-serif',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 4,
              transition: 'all 0.15s ease',
            }}
          >
            <span style={{ fontSize: 12 }}>{cat.icon}</span>
            <span>{cat.label}</span>
          </button>
        ))}
      </div>

      {/* Node List */}
      <div
        style={{
          flex: 1,
          overflow: 'auto',
          padding: '8px',
          display: 'flex',
          flexDirection: 'column',
          gap: 4,
        }}
      >
        {filteredNodes.map(node => (
          <DraggableNode
            key={node.label}
            node={node}
            onDragStart={onDragStart}
          />
        ))}
      </div>
    </div>
  );
}

interface DraggableNodeProps {
  node: PaletteNodeType;
  onDragStart: (nodeType: PaletteNodeType, event: React.DragEvent) => void;
}

function DraggableNode({ node, onDragStart }: DraggableNodeProps) {
  const [isDragging, setIsDragging] = useState(false);

  const handleDragStart = useCallback(
    (event: React.DragEvent) => {
      setIsDragging(true);
      event.dataTransfer.effectAllowed = 'copy';
      event.dataTransfer.setData('application/hiveos-node', JSON.stringify(node));
      onDragStart(node, event);
    },
    [node, onDragStart]
  );

  return (
    <div
      draggable
      onDragStart={handleDragStart}
      onDragEnd={() => setIsDragging(false)}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        padding: '8px 10px',
        background: isDragging
          ? 'var(--bg-surface-hover)'
          : 'transparent',
        border: `1px solid ${isDragging ? 'var(--border)' : 'transparent'}`,
        borderRadius: 8,
        cursor: 'grab',
        transition: 'all 0.12s ease',
        opacity: isDragging ? 0.7 : 1,
        userSelect: 'none',
      }}
      onMouseEnter={e => {
        if (!isDragging) {
          e.currentTarget.style.background = 'var(--bg-surface)';
        }
      }}
      onMouseLeave={e => {
        if (!isDragging) {
          e.currentTarget.style.background = 'transparent';
        }
      }}
    >
      {/* Icon circle */}
      <div
        style={{
          width: 28,
          height: 28,
          borderRadius: '50%',
          background: node.bgColor,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 13,
          flexShrink: 0,
        }}
      >
        {node.icon}
      </div>

      {/* Label + description */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            fontSize: 12,
            fontWeight: 510,
            color: 'var(--text-primary)',
            fontFamily: 'Inter Variable, Inter, system-ui, sans-serif',
            lineHeight: 1.3,
          }}
        >
          {node.label}
        </div>
        <div
          style={{
            fontSize: 10,
            color: 'var(--text-quaternary)',
            fontFamily: 'Inter Variable, Inter, system-ui, sans-serif',
            lineHeight: 1.3,
            marginTop: 1,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {node.description}
        </div>
      </div>

      {/* Drag handle */}
      <div
        style={{
          fontSize: 10,
          color: 'var(--text-quaternary)',
          opacity: 0.5,
        }}
      >
        ⠿
      </div>
    </div>
  );
}
