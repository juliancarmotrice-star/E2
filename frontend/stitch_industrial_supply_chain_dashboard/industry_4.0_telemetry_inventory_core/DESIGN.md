---
name: Industry 4.0 Telemetry & Inventory Core
colors:
  surface: '#0b1326'
  surface-dim: '#0b1326'
  surface-bright: '#31394d'
  surface-container-lowest: '#060e20'
  surface-container-low: '#131b2e'
  surface-container: '#171f33'
  surface-container-high: '#222a3d'
  surface-container-highest: '#2d3449'
  on-surface: '#dae2fd'
  on-surface-variant: '#bbcabf'
  inverse-surface: '#dae2fd'
  inverse-on-surface: '#283044'
  outline: '#86948a'
  outline-variant: '#3c4a42'
  surface-tint: '#4edea3'
  primary: '#4edea3'
  on-primary: '#003824'
  primary-container: '#10b981'
  on-primary-container: '#00422b'
  inverse-primary: '#006c49'
  secondary: '#4cd7f6'
  on-secondary: '#003640'
  secondary-container: '#03b5d3'
  on-secondary-container: '#00424e'
  tertiary: '#ffb95f'
  on-tertiary: '#472a00'
  tertiary-container: '#e29100'
  on-tertiary-container: '#523200'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#6ffbbe'
  primary-fixed-dim: '#4edea3'
  on-primary-fixed: '#002113'
  on-primary-fixed-variant: '#005236'
  secondary-fixed: '#acedff'
  secondary-fixed-dim: '#4cd7f6'
  on-secondary-fixed: '#001f26'
  on-secondary-fixed-variant: '#004e5c'
  tertiary-fixed: '#ffddb8'
  tertiary-fixed-dim: '#ffb95f'
  on-tertiary-fixed: '#2a1700'
  on-tertiary-fixed-variant: '#653e00'
  background: '#0b1326'
  on-background: '#dae2fd'
  surface-variant: '#2d3449'
typography:
  headline-xl:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.015em
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.005em
  headline-xl-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.015em
  body-lg:
    fontFamily: Inter
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 22px
  body-md:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  code-lg:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: -0.01em
  code-md:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0em
  code-sm:
    fontFamily: JetBrains Mono
    fontSize: 10px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: 0.02em
  label-md:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.04em
  label-sm:
    fontFamily: JetBrains Mono
    fontSize: 10px
    fontWeight: '600'
    lineHeight: 12px
    letterSpacing: 0.06em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 0.75rem
  gutter-desktop: 1rem
  margin: 0.75rem
  margin-desktop: 1.5rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.75rem
  space-lg: 1.25rem
  space-xl: 2rem
---

## Brand & Style

The design system embodies precision-grade Industry 4.0 cybernetics tailored for mission-critical supply chain engineering, warehousing automation, and ERP telemetry. The target audience comprises supply chain directors, warehouse dispatchers, demand forecasters, and logistics engineers managing fast-moving stock and volatile procurement cycles.

The aesthetic fuses **Utilitarian High-Density Minimalism** with **Technical Tactical Glassmorphism**. The visual field maintains deep optical focus through deep carbon and slate canvases, razor-sharp edge contrast, structural tabular figures, and calibrated chromatic indicators. It creates an atmosphere of complete operational control, real-time auditability, and immediate anomaly detection without cognitive fatigue. Micro-glow accents and high-visibility status semaphores provide continuous peripheral feedback on system health, stock velocity, and ledger parity.

## Colors

The color architecture is built strictly on an engineered dark spectrum designed for multi-monitor operations and high-stress control room environments:

- **Surface Tiers & Canvas**:
  - Deep Canvas: `#020617` (Slate-950) for core viewports.
  - Primary Structural Containers: `#0f172a` (Slate-900).
  - Raised Panel / Card Surfaces: `#1e293b` (Slate-800) with controlled alpha channels (`rgba(30, 41, 59, 0.7)` for frosted surfaces).
  - Outlines & Structural Ribs: `#334155` (Slate-700) and `#1e293b` (Slate-800) for interior cells.
- **State Semaphores & Telemetry**:
  - **Optimal Stock / System Nominal**: Emerald-400 (`#34d399`) and Emerald-500 (`#10b981`). Used for healthy batch statuses, positive cycle-counts, and balanced SKU coverage.
  - **Review / Buffer Warning**: Amber-400 (`#fbbf24`) and Amber-500 (`#f59e0b`). Emitted on lead-time degradation, reorder threshold proximity, and quarantine inspections.
  - **Critical Stockout / Discrepancy**: Rose-500 (`#f43f5e`) and Rose-600 (`#e11d48`). Strict triage priority for inventory stockouts, variance breaches, and reconciliation halts.
  - **Analytical / Telemetry Channel**: Cyan-400 (`#22d3ee`) and Blue-500 (`#3b82f6`). Dedicated to Pareto ABC/XYZ curves, lead-time distribution models, volumetric sensor outputs, and active SKU filters.
- **Data & Text Contrast**:
  - Primary Readout: `#f8fafc` (Slate-50) for primary metrics, serial markers, and high-value indicators.
  - Secondary Context: `#94a3b8` (Slate-400) for column definitions, schema keys, and auxiliary labels.
  - De-emphasized / Grid: `#475569` (Slate-600) for guide lines, empty slot counters, and disabled controls.

## Typography

The typographic hierarchy enforces a dual-engine structure:

1. **Inter (Interface & System Hierarchy)**: Powers structural headings, contextual descriptions, navigation anchors, and general UI controls. Engineered with optical kerning and tabular numeral alternatives (`tnum`) enabled system-wide.
2. **JetBrains Mono (Telemetry & Operational Tokens)**: Applied exclusively to numerical financial balances (e.g., Colombian Peso `COP $XX.XXX.XXX`), SKU tracking formats, internal batch hashes, timestamps, rack/aisle/bin coordinate vectors, and Pareto statistical percentages.

### Rules for Telemetry Formatting
- Currency amounts must include thousands separators (`.` in localized COP syntax) and display strictly in monospaced weights to prevent vertical shifting during live websocket streams.
- Status chips and micro-labels utilize uppercase rendering with distinct positive tracking (`0.04em` to `0.06em`) for rapid identification in peripheral vision.

## Layout & Spacing

This design system uses a 12-column dense fluid grid with responsive sidebars and dynamic viewports engineered for data-dense monitoring panels.

### Form Factor Behavior
- **Desktop (>= 1280px)**: 12-column fluid grid. Component gaps anchor to `0.75rem` (`space-md`) for extreme data density without clipping. Outer margin defaults to `1.5rem`. Lateral navigation collapses into high-density icon strips with flyout drawers.
- **Tablet (768px - 1279px)**: 8-column layout. Analytical Pareto charts dynamically stack above inventory reconciliation tables. Secondary telemetry metrics collapse into swipeable inline metric rails.
- **Mobile (< 768px)**: 4-column layout. High-density data grids transition to stacked tactical record cards. Critical operational actions (Confirm Pick, Flag Stockout, Cycle Count Entry) snap to a thumb-optimized bottom control dock with fixed 48px touch barriers.

### Spatial Rhythm
- Interior table cells and metric rows must respect strict micro-vertical paddings (`space-xs` and `space-sm`) to maximize visible records above the fold.
- Section boundaries and separate functional domains (e.g., Telemetry Feed vs. Order Execution) are isolated by `space-lg` or rigid 1px structural borders rather than large empty white space.

## Elevation & Depth

Visual hierarchy does not use soft diffuse drop shadows. Instead, it relies on **engineered glassmorphism**, **chromatic edge refraction**, and **ambient glow halos**.

### Elevation Stack
- **Level 0 (Canvas Base)**: `#020617` solid. Non-interactive background substrate.
- **Level 1 (Docked Data Tables & Metric Panels)**: Solid `#0f172a` with a 1px border of `rgba(51, 65, 85, 0.4)` (Slate-700/40).
- **Level 2 (Active Glassmorphic Overlays & Filter Strips)**: `rgba(15, 23, 42, 0.75)` with `backdrop-filter: blur(12px)` and a top edge highlight of `1px solid rgba(255, 255, 255, 0.08)`.
- **Level 3 (Diagnostic Drawers, Modals & Floating Popovers)**: `rgba(30, 41, 59, 0.95)` with `backdrop-filter: blur(16px)`, outlined with `1px solid rgba(148, 163, 184, 0.15)` and accompanied by an ambient structural occlusion: `box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.6), 0 8px 10px -6px rgba(0, 0, 0, 0.6)`.

### Tactical Glow Micro-Accents
- **Optimal / Connected**: Subtle radial emission `0 0 12px rgba(16, 185, 129, 0.25)`.
- **Telemetry Query / Analytics Focus**: `0 0 12px rgba(6, 182, 212, 0.25)`.
- **Variance Out-of-Bounds / Alert**: Pulsing edge bloom `0 0 14px rgba(244, 63, 94, 0.35)`.

## Shapes

The interface embraces a **Soft/Technical** corner syntax (`roundedness: 1`). Radii are strictly kept compact:
- Core inputs, data cells, badges, and primary buttons conform to `0.25rem` (4px).
- Metric modules, cards, and modal canvases conform to `0.5rem` (8px).
- Floating contextual tooltips and inline telemetry pill tags scale down to `0.25rem` (4px).

Pill shapes and organic, heavily rounded forms are prohibited. The visual language favors structural architectural forms that convey engineering rigor and spatial efficiency.

## Components

### Buttons & Interactive Triggers
- **Primary Operational Action**: Solid Emerald-500 (`#10b981`) text on deep surface, or `#10b981` solid background with `#020617` bold typography. Hover applies `#34d399` and an ambient green glow. Minimum hit area: desktop 32px height (dense), mobile 48px height.
- **Secondary / Data Analysis Action**: `#0f172a` base, 1px border `#334155`, text `#e2e8f0`. Hover transitions border to Cyan-400 with faint cyan fill tint (`rgba(6, 182, 212, 0.05)`).
- **Destructive / Variance Quarantine**: Crimson base with Rose-500 border and glowing micro-outline on active tap.

### Status Chips & Telemetry Badges
- Composed using `code-sm` JetBrains Mono, uppercase.
- Built as inline-flex items with an integrated 6px pulsing LED status beacon.
- Backgrounds are 10% opacity fills corresponding to the semaphore color, bordered with 20% opacity strokes (e.g., Alert: `bg-rose-500/10 text-rose-400 border border-rose-500/20`).

### High-Density Data Tables
- Row height: 36px default, 44px mobile view.
- Alternating subtle zebra striping (`#0f172a` and `rgba(30, 41, 59, 0.3)`).
- Borders: Horizontal only, 1px `rgba(51, 65, 85, 0.4)`. No vertical column separator lines; alignment is handled via strict tabular columns and monospaced right-aligned figures.
- Sticky column headers rendered in `label-sm` Slate-400 with active sort vectors highlighted in Cyan-400.

### Input Fields & Search Shells
- Background: `#020617` (inset depth effect).
- Border: 1px `#334155`. Focus state triggers a clean 1px Cyan-400 stroke and `0 0 0 1px #06b6d4` without fuzzy outer rings.
- Integrated barcode scanner shortcut keys and search syntax tags rendered in JetBrains Mono.

### Telemetry Cards & Pareto Analytics Containers
- Structural base: Frosted Slate-800 (`rgba(30, 41, 59, 0.7)`), 1px border `#334155/60`.
- Interior header: Displays the technical subsystem code (e.g., `SYS-INV-BOG-01`) alongside a real-time websocket latency badge.
- Chart canvas: Vector lines rendered with 1.5px stroke width; active plot nodes feature glowing circular markers with numeric tooltips anchored to the pointer.

### Checkboxes & Segmented Toggles
- Checkboxes: 16x16px squares with 2px corner radius. Slate-950 fill, Slate-600 border. Checked state fills with Emerald-500, displaying a dark high-contrast check icon.
- Radio buttons: Multi-state industrial selectors styled as joined segmented pill-bars with an active Slate-700 illuminated tile.