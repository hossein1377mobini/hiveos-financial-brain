import { FlowCanvas } from './components/FlowCanvas';

export default function App() {
  return (
    <div style={{ width: '100vw', height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Minimal top bar */}
      <div
        style={{
          height: 36,
          background: 'var(--bg-deep)',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          padding: '0 16px',
          flexShrink: 0,
          gap: 12,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}
        >
          <span style={{ fontSize: 16 }}>🐝</span>
          <span
            style={{
              fontSize: 13,
              fontWeight: 510,
              color: 'var(--text-primary)',
              fontFamily: 'Inter Variable, Inter, system-ui, sans-serif',
              letterSpacing: '-0.3px',
            }}
          >
            HiveOS
          </span>
          <span
            style={{
              fontSize: 10,
              color: 'var(--text-quaternary)',
              fontFamily: 'var(--font-mono)',
              background: 'rgba(255,255,255,0.04)',
              padding: '1px 6px',
              borderRadius: 4,
            }}
          >
            Playground
          </span>
        </div>

        <div style={{ flex: 1 }} />

        <span
          style={{
            fontSize: 11,
            color: 'var(--text-quaternary)',
            fontFamily: 'var(--font-mono)',
          }}
        >
          v0.12.0-dev
        </span>
      </div>

      {/* Main Playground */}
      <FlowCanvas />
    </div>
  );
}
