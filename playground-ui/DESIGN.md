---
version: alpha
name: HiveOS-Playground-Linear
description: >
  HiveOS Playground design language — inspired by Linear's dark-mode-native
  precision engineering. Near-black canvas (#08090a) where content emerges
  from darkness. Brand indigo-violet accent (#5e6ad2 / #7170ff). Inter
  Variable at weight 510 as the signature UI weight.
colors:
  bg-deep: "#08090a"
  bg-panel: "#0f1011"
  bg-surface: "#191a1b"
  bg-surface-hover: "#28282c"
  text-primary: "#f7f8f8"
  text-secondary: "#d0d6e0"
  text-tertiary: "#8a8f98"
  text-quaternary: "#62666d"
  brand: "#5e6ad2"
  brand-accent: "#7170ff"
  brand-hover: "#828fff"
  success: "#10b981"
  warning: "#f59e0b"
  error: "#ef4444"
  border: "rgba(255,255,255,0.08)"
  border-subtle: "rgba(255,255,255,0.05)"
  border-strong: "#23252a"
  overlay: "rgba(0,0,0,0.85)"
  selection-bg: "#5e6ad2"
  selection-fg: "#ffffff"
  node-trigger: "#10b981"
  node-action: "#7170ff"
  node-ai: "#f59e0b"
  node-flow: "#8a8f98"
typography:
  display-xl:
    fontFamily: Inter Variable, Inter, system-ui, sans-serif
    fontSize: 48px
    fontWeight: 510
    lineHeight: 1.0
    letterSpacing: -1.056px
  display-lg:
    fontFamily: Inter Variable, Inter, system-ui, sans-serif
    fontSize: 32px
    fontWeight: 400
    lineHeight: 1.13
    letterSpacing: -0.704px
  heading:
    fontFamily: Inter Variable, Inter, system-ui, sans-serif
    fontSize: 20px
    fontWeight: 590
    lineHeight: 1.33
    letterSpacing: -0.24px
  body:
    fontFamily: Inter Variable, Inter, system-ui, sans-serif
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.5
  body-medium:
    fontFamily: Inter Variable, Inter, system-ui, sans-serif
    fontSize: 14px
    fontWeight: 510
    lineHeight: 1.5
  code:
    fontFamily: JetBrains Mono, ui-monospace, SFMono-Regular, Menlo, monospace
    fontSize: 13px
    fontWeight: 400
    lineHeight: 1.5
  caption:
    fontFamily: Inter Variable, Inter, system-ui, sans-serif
    fontSize: 12px
    fontWeight: 400
    lineHeight: 1.4
  caption-medium:
    fontFamily: Inter Variable, Inter, system-ui, sans-serif
    fontSize: 12px
    fontWeight: 510
    lineHeight: 1.4
  label:
    fontFamily: Inter Variable, Inter, system-ui, sans-serif
    fontSize: 11px
    fontWeight: 510
    lineHeight: 1.4
rounded:
  none: 0px
  sm: 4px
  md: 6px
  lg: 8px
  xl: 12px
  xxl: 16px
  full: 9999px
spacing:
  xxs: 4px
  xs: 8px
  sm: 12px
  md: 16px
  lg: 24px
  xl: 32px
  xxl: 40px
  section: 80px
components:
  button-primary:
    backgroundColor: "{colors.brand}"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
    padding: "{spacing.xs} {spacing.md}"
    border: none
  button-ghost:
    backgroundColor: "rgba(255,255,255,0.02)"
    textColor: "{colors.text-secondary}"
    rounded: "{rounded.md}"
    border: "1px solid {colors.border}"
    padding: "{spacing.xs} {spacing.md}"
  card:
    backgroundColor: "{colors.bg-surface}"
    border: "1px solid {colors.border}"
    rounded: "{rounded.lg}"
  input:
    backgroundColor: "rgba(255,255,255,0.02)"
    textColor: "{colors.text-primary}"
    border: "1px solid {colors.border}"
    rounded: "{rounded.md}"
    padding: "{spacing.sm} {spacing.md}"
  nav-bar:
    backgroundColor: "{colors.bg-panel}"
    border: "1px solid {colors.border-subtle}"
    height: 48px
  node-trigger:
    backgroundColor: "rgba(16,185,129,0.1)"
    borderColor: "{colors.node-trigger}"
    textColor: "{colors.success}"
  node-action:
    backgroundColor: "rgba(113,112,255,0.1)"
    borderColor: "{colors.node-action}"
    textColor: "{colors.brand-accent}"
  node-ai:
    backgroundColor: "rgba(245,158,11,0.1)"
    borderColor: "{colors.node-ai}"
    textColor: "{colors.warning}"
  node-flow:
    backgroundColor: "rgba(138,143,152,0.1)"
    borderColor: "{colors.node-flow}"
    textColor: "{colors.text-tertiary}"
---
