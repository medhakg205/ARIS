# ARIS Frontend Architecture

**Adaptive Runtime Intelligence System for Embedded Devices**
**Subsystem Owner:** Engineer 3 (AI + Frontend)
**Version:** 1.0.0

---

## 1. Overview

The ARIS frontend is a single-page React/TypeScript application that serves as the operational interface for embedded firmware optimization on Arduino-class microcontrollers. It is designed to look and behave like an embedded profiler and hardware diagnostics tool — not generic AI software.

### Technology Stack
| Layer | Technology |
|---|---|
| UI Framework | React 18.3 |
| Language | TypeScript (strict mode) |
| Build | Vite |
| Styling | Tailwind CSS (dark theme) |
| Charts | Recharts |
| Icons | Lucide React |
| Desktop Shell | Electron |
| Testing | Vitest + @testing-library/react |

---

## 2. Application Architecture

```
aris_desktop/src/
├── App.tsx                          # Root component, screen routing, global state
├── main.tsx                         # React entry point
├── index.css                        # Tailwind base + custom styles
├── types/
│   └── index.ts                     # Canonical TypeScript types (matches backend exactly)
├── services/
│   ├── api.ts                       # REST client (all 18+ endpoints)
│   └── websocket.ts                 # WebSocket client with auto-reconnect
├── hooks/
│   └── useAris.ts                   # Main state hook (useARIS)
└── components/
    ├── Navbar.tsx                    # Top navigation + connection status + demo banner
    ├── common/
    │   ├── MetricBadge.tsx           # Metric value + unit + veracity classification badge
    │   ├── ErrorBanner.tsx           # ARIS_* error code display
    │   └── DemoBanner.tsx            # Persistent DEMO MODE indicator
    ├── Dashboard/
    │   └── DashboardView.tsx         # Board status, key metrics, run state, quick links
    ├── LiveMonitor/
    │   └── LiveMonitorView.tsx       # Real-time WebSocket telemetry charts
    ├── Firmware/
    │   └── FirmwareView.tsx          # Upload, edit, manage firmware
    ├── Analysis/
    │   └── AnalysisView.tsx          # Findings table with severity/correlation filters
    ├── Optimization/
    │   └── OptimizationView.tsx      # Before/after code diff, approval workflow
    ├── Experiments/
    │   └── ExperimentsView.tsx       # Pipeline step visualizer
    ├── Validation/
    │   └── ValidationView.tsx        # Baseline vs candidate comparison
    ├── History/
    │   └── HistoryView.tsx           # Past experiments log
    └── Settings/
        └── SettingsView.tsx          # Backend, board, serial, AI, demo config
```

---

## 3. Data Flow

```
┌──────────────┐    REST API     ┌─────────────────────┐
│  ARIS Backend ├───────────────►│  services/api.ts    │
│  (port 8765)  │                │  (fetch + error)     │
│               │    WebSocket   ├─────────────────────┤
│  /ws/telemetry├───────────────►│  services/websocket │
│  /{run_id}    │   (auto-recon) │  (ARISWebSocket)     │
└──────────────┘                └────────┬────────────┘
                                         │
                                         ▼
                                ┌─────────────────────┐
                                │  hooks/useARIS.ts    │
                                │  (central state hub) │
                                └────────┬────────────┘
                                         │
                           ┌─────────────┼──────────────┐
                           ▼             ▼              ▼
                      ┌────────┐   ┌──────────┐   ┌──────────┐
                      │ Screen │   │  Screen  │   │  Screen  │
                      │ Views  │   │  Views   │   │  Views   │
                      └────────┘   └──────────┘   └──────────┘
```

### State Management
The `useARIS()` hook is the single source of truth:
- Polls backend health every 10 seconds
- Manages WebSocket lifecycle (connect when run starts, disconnect when stopped)
- Maintains per-metric telemetry history (capped at 200 samples per metric)
- Exposes all CRUD actions as async callbacks
- Tracks loading states per operation
- Captures errors as `ARISApiError` instances with canonical error codes

---

## 4. Screen Descriptions

### 4.1 Dashboard (`DashboardView`)
- Board info strip (MCU, architecture, clock, GPIO)
- Connection + run status bar
- 8 key metric badges with veracity classification
- Hardware specification panel
- Quick-link cards to other screens

### 4.2 Live Monitor (`LiveMonitorView`)
- WebSocket connection status bar
- 4 primary timeline charts (loop_time, cpu_load, sram_free, interrupt_rate) via Recharts
- Each chart labeled with its classification (MEASURED/ESTIMATED/DERIVED)
- 6 secondary metric badges
- Sequence counter and SIMULATED badge when in demo mode

### 4.3 Firmware (`FirmwareView`)
- Left panel: code editor (textarea) with line count and byte size
- Right panel: firmware library list with selection
- Upload toolbar with board target display
- Example sketch pre-loaded for quick demo

### 4.4 Analysis (`AnalysisView`)
- Severity distribution bar (CRITICAL/HIGH/MEDIUM/LOW/INFO counts)
- Correlation filter (ALL/HIGH/MEDIUM/LOW/NONE)
- Expandable finding rows with evidence JSON, description, recommended action
- "Generate Optimization Candidate" button on each finding

### 4.5 Optimization (`OptimizationView`)
- Left sidebar: candidate list with status + risk badges
- Main panel: full detail (problem, before/after code, rationale, hardware consideration)
- Expected effect section with PREDICTED classification badges
- **Mandatory human approval workflow**: Propose → Confirm Approve / Reject
- Status-aware: shows contextual messages for APPROVED, VALIDATED, etc.

### 4.6 Experiments (`ExperimentsView`)
- Pipeline step visualizer: CREATED → BUILDING → FLASHING → RUNNING → COLLECTING → COMPARING → VALIDATED
- Auto-refresh every 5 seconds while experiments are running
- Optimization reference and run ID links
- Navigate to validation results

### 4.7 Validation (`ValidationView`)
- Baseline vs candidate run ID display
- Metric comparison table with absolute/percentage deltas and IMPROVED/REGRESSION badges
- Prediction vs Reality section:
  - Per-metric predicted vs actual values
  - Directional match indicator
  - Composite prediction accuracy score
  - Scientific caveat about single-trial significance

### 4.8 History (`HistoryView`)
- Searchable, sortable experiment log
- Status filter (ALL/COMPLETED/RUNNING/CREATED/FAILED)
- Validation status badges
- Links to detailed validation results

### 4.9 Settings (`SettingsView`)
- Backend connection probe
- Board selection (visual cards)
- Serial port selection + baud rate + connect/disconnect
- AI provider status list (Gemini, OpenAI, Rule Synthesizer)
- Demo mode start/stop

---

## 5. Design System

### Color Palette
| Element | Color | Hex |
|---|---|---|
| Background | Near-black | `#0a0d14` |
| Surface | Dark slate | `bg-slate-900/60` |
| Border | Subtle slate | `border-slate-800` |
| Text Primary | Light slate | `text-slate-100` |
| Text Secondary | Mid slate | `text-slate-400` |
| Text Muted | Dark slate | `text-slate-500` |
| Accent | Cyan | `text-cyan-400` |
| Success | Emerald | `text-emerald-400` |
| Warning | Amber | `text-amber-400` |
| Error | Red | `text-red-400` |

### Typography
- **Font**: System monospace (`font-mono`) throughout
- **Sizes**: `text-[9px]` for labels, `text-xs`/`text-sm` for content, `text-xl` for values

### Veracity Classification Colors
| Classification | Color | Usage |
|---|---|---|
| MEASURED | Emerald | Hardware-read values |
| ESTIMATED | Amber | Calculated from indirect evidence |
| DERIVED | Cyan | Computed from other metrics |
| PREDICTED | Purple | AI-forecasted before hardware test |

---

## 6. Error Handling

### Canonical Error Codes
All errors use the ARIS canonical error schema with human-readable titles and recovery hints:

| Code | Title | Recovery Hint |
|---|---|---|
| `ARIS_SERIAL_DISCONNECTED` | Serial Connection Lost | Check USB cable, reconnect from Settings |
| `ARIS_BOARD_NOT_FOUND` | Board Not Found | Check serial port selection |
| `ARIS_AI_UNAVAILABLE` | AI Engine Unavailable | Configure API key or use Rule Synthesizer |
| `ARIS_OPTIMIZATION_INVALID` | Invalid Optimization | AI output failed schema validation |
| `ARIS_BACKEND_UNAVAILABLE` | Backend Unavailable | Start server on port 8765 |

### Error Display
- `ErrorBanner` component shows at page-top with dismiss button
- Inline error banners within specific views (e.g., firmware upload errors)
- WebSocket errors propagated through the `WsMessage` type

---

## 7. Demo Mode

Demo mode is a first-class feature, never hidden:
- `DemoBanner` shown persistently in navbar and status bar
- All telemetry samples from demo runs marked with source: `SIMULATOR`
- `SIMULATED` badge on Live Monitor charts
- Demo started via Dashboard "Start Demo Run" or Settings "Start Demo Run"
- Never silently mixed with physical hardware telemetry

---

## 8. WebSocket Protocol

### Connection
- URL: `ws://127.0.0.1:8765/ws/telemetry/{run_id}`
- Fallback: `ws://127.0.0.1:8765/ws/telemetry`
- Auto-reconnect with exponential backoff (500ms → 8000ms max)

### Message Types
```typescript
type WsMessage =
  | { type: 'TELEMETRY_UPDATE'; data: TelemetrySample; source: string }
  | { type: 'RUN_STATUS'; data: RunRecord; source: string }
  | { type: 'ERROR'; data: ArisError; source: string }
  | { type: 'CONNECTION_STATE'; connected: boolean; reason?: string }
```

### Telemetry Buffering
- Latest sample per metric stored in `latestSamples` (flat map)
- History per metric capped at 200 samples in `telemetryHistory`
- Sequence numbers tracked for out-of-order detection

---

## 9. Security Invariants

1. **NEVER automatically flash AI-generated code** — users must explicitly approve
2. **Never mix synthetic and physical telemetry silently** — DEMO MODE always visible
3. **`cpu_load` on ATmega328P/ATmega2560 is always ESTIMATED** — no hardware perf counters
4. **Never disable buttons silently** — show canonical error if action unavailable
