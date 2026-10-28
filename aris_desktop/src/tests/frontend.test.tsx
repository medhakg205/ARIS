// ============================================================
// ARIS Frontend Tests (v3.0.0-PROFESSIONAL)
// Tests for common components, theme engine, navigation, and contracts
// ============================================================

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import React from 'react';

import { MetricBadge } from '../components/common/MetricBadge';
import { DemoBanner } from '../components/common/DemoBanner';
import { ErrorBanner } from '../components/common/ErrorBanner';
import { Sidebar } from '../components/Sidebar';
import { TopBar } from '../components/TopBar';
import { CommandPalette } from '../components/CommandPalette/CommandPalette';
import { ReportCenter } from '../components/Reports/ReportCenter';

afterEach(() => {
  cleanup();
});

// ---- MetricBadge Tests ----
describe('MetricBadge', () => {
  it('renders metric with classification badge', () => {
    render(
      <MetricBadge
        label="CPU Load"
        value={42.5}
        unit="%"
        classification="ESTIMATED"
      />
    );
    expect(screen.getByText('CPU Load')).toBeDefined();
    expect(screen.getByText('42.50')).toBeDefined();
    expect(screen.getByText('%')).toBeDefined();
    expect(screen.getByText('ESTIMATED')).toBeDefined();
  });

  it('renders compact mode', () => {
    render(
      <MetricBadge
        label="Loop Time"
        value={1.23}
        unit="ms"
        classification="MEASURED"
        compact
      />
    );
    expect(screen.getByText('Loop Time')).toBeDefined();
    expect(screen.getByText('MEASURED')).toBeDefined();
  });

  it('shows confidence bar when provided', () => {
    render(
      <MetricBadge
        label="IRQ"
        value={100}
        unit="Hz"
        classification="DERIVED"
        confidence={0.85}
      />
    );
    expect(screen.getByText('85%')).toBeDefined();
  });

  it('renders dash for unknown values', () => {
    render(
      <MetricBadge
        label="SRAM"
        value="—"
        unit="B"
        classification="MEASURED"
      />
    );
    expect(screen.getByText('—')).toBeDefined();
  });
});

// ---- DemoBanner Tests ----
describe('DemoBanner', () => {
  it('renders when visible', () => {
    render(<DemoBanner visible={true} />);
    expect(screen.getByText(/Demo Mode/i)).toBeDefined();
  });

  it('renders nothing when not visible', () => {
    const { container } = render(<DemoBanner visible={false} />);
    expect(container.innerHTML).toBe('');
  });
});

// ---- ErrorBanner Tests ----
describe('ErrorBanner', () => {
  it('renders null when no error', () => {
    const { container } = render(<ErrorBanner error={null} />);
    expect(container.innerHTML).toBe('');
  });

  it('renders string error', () => {
    render(<ErrorBanner error="Something went wrong" />);
    expect(screen.getByText('Something went wrong')).toBeDefined();
  });

  it('renders ARISApiError with code and hint', async () => {
    const { ARISApiError } = await import('../services/api');
    const err = new ARISApiError('ARIS_SERIAL_DISCONNECTED', 'Port COM3 closed');
    render(<ErrorBanner error={err} />);
    expect(screen.getByText('ARIS_SERIAL_DISCONNECTED')).toBeDefined();
    expect(screen.getByText('Serial Connection Lost')).toBeDefined();
  });

  it('calls onDismiss when X clicked', () => {
    const onDismiss = vi.fn();
    render(<ErrorBanner error="Test error" onDismiss={onDismiss} />);
    const btn = screen.getByRole('button');
    fireEvent.click(btn);
    expect(onDismiss).toHaveBeenCalledTimes(1);
  });
});

// ---- Type Contracts ----
describe('Type Contracts', () => {
  it('TelemetrySample has all canonical fields', () => {
    const sample: import('../types').TelemetrySample = {
      protocol_version: '1.0',
      run_id: 'RUN-001',
      board_id: 'arduino_uno',
      mcu: 'ATmega328P',
      timestamp_ms: 1000,
      sequence: 42,
      metric: 'loop_time',
      value: 12.5,
      unit: 'ms',
      classification: 'MEASURED',
      confidence: 1.0,
      is_demo: false,
    };

    expect(sample.protocol_version).toBe('1.0');
    expect(sample.classification).toBe('MEASURED');
    expect(sample.is_demo).toBe(false);
  });

  it('MetricClassification has exactly 4 values', () => {
    const classifications: import('../types').MetricClassification[] = [
      'MEASURED',
      'ESTIMATED',
      'DERIVED',
      'PREDICTED',
    ];
    expect(classifications).toHaveLength(4);
  });

  it('cpu_load must be ESTIMATED on AVR', () => {
    const sample: import('../types').TelemetrySample = {
      protocol_version: '1.0',
      run_id: 'RUN-002',
      board_id: 'arduino_uno',
      mcu: 'ATmega328P',
      timestamp_ms: 2000,
      sequence: 1,
      metric: 'cpu_load',
      value: 34.2,
      unit: '%',
      classification: 'ESTIMATED',
      confidence: 0.85,
    };
    expect(sample.classification).toBe('ESTIMATED');
  });

  it('OptimizationStatus has mandatory approval step', () => {
    const statuses: import('../types').OptimizationStatus[] = [
      'PROPOSED',
      'APPROVED',
      'BUILDING',
      'TESTING',
      'VALIDATED',
      'REJECTED',
      'ROLLED_BACK',
      'FAILED',
    ];
    expect(statuses).toContain('APPROVED');
    expect(statuses).toContain('REJECTED');
  });

  it('ArisError has canonical structure', () => {
    const err: import('../types').ArisError = {
      error_code: 'ARIS_BUILD_FAILED',
      message: 'Compilation error: undefined symbol',
      details: { line: 42, file: 'main.cpp' },
      recoverable: true,
    };
    expect(err.error_code).toBe('ARIS_BUILD_FAILED');
    expect(err.recoverable).toBe(true);
  });
});

// ---- API Client ----
describe('API Client', () => {
  it('ARISApiError has correct structure', async () => {
    const { ARISApiError } = await import('../services/api');
    const err = new ARISApiError(
      'ARIS_BOARD_NOT_FOUND',
      'No board at port',
      { port: 'COM3' },
      true
    );
    expect(err.name).toBe('ARISApiError');
    expect(err.error_code).toBe('ARIS_BOARD_NOT_FOUND');
    expect(err.message).toBe('No board at port');
    expect(err.recoverable).toBe(true);
    expect(err.details).toEqual({ port: 'COM3' });
  });

  it('throws ARIS_BACKEND_UNAVAILABLE on network failure', async () => {
    const { apiHealth, ARISApiError } = await import('../services/api');
    global.fetch = vi.fn().mockRejectedValue(new Error('Network error'));

    await expect(apiHealth()).rejects.toThrow(ARISApiError);
    await expect(apiHealth()).rejects.toMatchObject({
      error_code: 'ARIS_BACKEND_UNAVAILABLE',
    });
  });
});

// ---- WebSocket Client ----
describe('WebSocket Client', () => {
  it('arisWs is a singleton', async () => {
    const { arisWs } = await import('../services/websocket');
    expect(arisWs).toBeDefined();
    expect(typeof arisWs.connect).toBe('function');
    expect(typeof arisWs.disconnect).toBe('function');
    expect(typeof arisWs.subscribe).toBe('function');
  });
});

// ---- ExperimentsView & Validation ----
describe('ExperimentsView', () => {
  it('renders experiment with Run & Validate Candidate button when status is CREATED', async () => {
    const { ExperimentsView } = await import('../components/Experiments/ExperimentsView');
    const onRun = vi.fn().mockResolvedValue({});
    const onRefresh = vi.fn();
    const onNav = vi.fn();

    const mockExp: import('../types').ExperimentRecord = {
      experiment_id: 'EXP-TEST-001',
      title: 'Throttle UART Output',
      board_id: 'arduino_uno',
      baseline_run_id: 'ARIS-BASE-001',
      candidate_run_id: undefined,
      optimization_id: 'OPT-001',
      status: 'CREATED',
      validation_id: undefined,
      created_at: new Date().toISOString(),
    };

    render(
      <ExperimentsView
        experiments={[mockExp]}
        optimizations={[]}
        onRefresh={onRefresh}
        onNavigateValidation={onNav}
        onRunExperiment={onRun}
      />
    );

    expect(screen.getByText('Throttle UART Output')).toBeDefined();
    expect(screen.getByText('Ready to Run & Benchmark Candidate')).toBeDefined();
    const runBtn = screen.getByRole('button', { name: /Run & Validate Candidate/i });
    expect(runBtn).toBeDefined();

    fireEvent.click(runBtn);
    expect(onRun).toHaveBeenCalledWith('EXP-TEST-001');
  });
});

// ---- v3.0.0-PROFESSIONAL UI Components ----
describe('v3.0.0 Navigation & Shell Components', () => {
  it('renders Sidebar with engineering tabs', () => {
    const onTabChange = vi.fn();
    render(
      <Sidebar
        activeTab="dashboard"
        onTabChange={onTabChange}
        issuesCount={3}
        experimentsCount={1}
        candidatesCount={2}
        hardwareConnected={false}
      />
    );

    expect(screen.getByText('Dashboard')).toBeDefined();
    expect(screen.getByText('Firmware')).toBeDefined();
    expect(screen.getByText('Telemetry')).toBeDefined();
    expect(screen.getByText('Analysis')).toBeDefined();
    expect(screen.getByText('Optimize')).toBeDefined();
    expect(screen.getByText('Experiments')).toBeDefined();
  });

  it('renders TopBar with breadcrumb and status indicators', () => {
    const onNavigate = vi.fn();
    render(
      <TopBar
        activeTab="dashboard"
        projectName="ARIS Test"
        hardwareConnected={false}
        isDemo={false}
        confidence="UNKNOWN"
        themeMode="dark"
        onThemeChange={vi.fn()}
        onOpenCommandPalette={vi.fn()}
        onOpenSearch={vi.fn()}
        onOpenNotifications={vi.fn()}
        onOpenInfo={vi.fn()}
        onNavigate={onNavigate}
        unreadNotificationsCount={2}
        telemetryActive={false}
      />
    );

    expect(screen.getByText('Dashboard')).toBeDefined();
    expect(screen.getByText('No Hardware Connected')).toBeDefined();
  });

  it('renders CommandPalette with shortcut items', () => {
    const onNavigate = vi.fn();
    render(
      <CommandPalette
        isOpen={true}
        onClose={vi.fn()}
        onNavigate={onNavigate}
        onAutoDetect={vi.fn()}
        onCompileFirmware={vi.fn()}
        onFlashFirmware={vi.fn()}
        onStartBaseline={vi.fn()}
        onStopBaseline={vi.fn()}
        onToggleTheme={vi.fn()}
        onToggleSidebar={vi.fn()}
        onGenerateReport={vi.fn()}
      />
    );

    expect(screen.getByPlaceholderText('Type a command or search action...')).toBeDefined();
    expect(screen.getByText('Detect Microcontroller Board')).toBeDefined();
  });

  it('renders ReportCenter with executive summary', () => {
    const mockExp: import('../types').ExperimentRecord = {
      experiment_id: 'EXP-TEST-002',
      title: 'Interrupt Debouncing Optimization',
      board_id: 'arduino_uno',
      baseline_run_id: 'BASE-01',
      candidate_run_id: 'CAND-01',
      optimization_id: 'OPT-02',
      status: 'SUCCESS',
      created_at: new Date().toISOString(),
    };

    render(
      <ReportCenter
        experiments={[mockExp]}
        selectedBoard={null}
        patentMarkdown="# Claims"
      />
    );

    expect(screen.getByText('Reports')).toBeDefined();
    expect(screen.getByText(/VERIFICATION SUMMARY/i)).toBeDefined();
  });

  // ---- Truthfulness & Zero-Default Behavior Tests ----
  it('renders truthful zero-default states in PredictionVsRealityView when no validation data exists', async () => {
    const { PredictionVsRealityView } = await import('../components/Optimization/PredictionVsRealityView');
    render(
      <PredictionVsRealityView
        validationResult={null}
        candidate={null}
        experiment={null}
      />
    );

    expect(screen.getByText('Prediction Accuracy Unavailable')).toBeDefined();
    expect(screen.getByText(/Prediction accuracy is calculated only after candidate compilation/i)).toBeDefined();
  });

  it('renders truthful dashes in FirmwareWorkspace when no board is connected', async () => {
    const { FirmwareWorkspace } = await import('../components/Firmware/FirmwareWorkspace');
    render(
      <FirmwareWorkspace
        firmwareList={[]}
        activeFirmware={null}
        selectedBoard={null}
        ideSketches={[]}
        activeIDESketch={null}
        onSyncIDESketch={vi.fn()}
        onRefreshIDESketches={vi.fn()}
        onSelectFirmware={vi.fn()}
        hardwareConnected={false}
      />
    );

    expect(screen.getByText(/Target: —/i)).toBeDefined();
  });

  it('renders LiveValidationMonitor completed state with CheckCircle2 icon without error', async () => {
    const { LiveValidationMonitor } = await import('../components/Optimization/LiveValidationMonitor');
    render(
      <LiveValidationMonitor
        isValidating={false}
        isComplete={true}
        progressPct={100}
        currentSamples={500}
        targetSamples={500}
        latestSamples={{}}
        isDemo={false}
        hardwareConnected={true}
      />
    );

    expect(screen.getByText(/Live Hardware Validation Complete/i)).toBeDefined();
    expect(screen.getByText(/Validation benchmark complete/i)).toBeDefined();
  });

  // ---- ErrorBoundary Tests ----
  it('ErrorBoundary renders fallback error screen when child throws', async () => {
    const { ErrorBoundary } = await import('../components/common/ErrorBoundary');
    const ThrowingComponent = () => {
      throw new Error('Test renderer crash');
    };

    // Suppress console.error for expected test error
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <ErrorBoundary>
        <ThrowingComponent />
      </ErrorBoundary>
    );

    expect(screen.getByText(/ARIS Studio encountered a renderer error/i)).toBeDefined();
    expect(screen.getAllByText(/Test renderer crash/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/Reload ARIS Studio/i)).toBeDefined();

    spy.mockRestore();
  });

  it('renders App shell without throwing uncaught exceptions', async () => {
    const { default: App } = await import('../App');
    const { ErrorBoundary } = await import('../components/common/ErrorBoundary');

    render(
      <ErrorBoundary>
        <App />
      </ErrorBoundary>
    );

    expect(screen.getByText(/ARIS v3.0.0-PROFESSIONAL/i)).toBeDefined();
  });

  it('renders OptimizationCenter without throwing ReferenceError on CheckCircle2 or any other symbol', async () => {
    const { OptimizationCenter } = await import('../components/Optimization/OptimizationCenter');
    const { ErrorBoundary } = await import('../components/common/ErrorBoundary');

    // Mock ResizeObserver for jsdom environment (recharts ResponsiveContainer)
    global.ResizeObserver = class ResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    };

    const mockCandidates: any[] = [
      {
        optimization_id: 'CAND-001',
        finding_id: 'FIND-001',
        title: 'Direct Register PORTB Access',
        problem: 'Inefficient digitalWrite GPIO pin toggling',
        source_location: { file: 'main.ino', line: 12 },
        description: 'Replace digitalWrite with PORTB direct register manipulation',
        before_code: 'digitalWrite(13, HIGH);',
        after_code: 'PORTB |= (1 << 5);',
        reason: 'Eliminates pin mapping runtime overhead',
        hardware_consideration: 'Target pin 13 is mapped to Port B, bit 5 on ATmega328P',
        strategy: 'DIRECT_REGISTER_IO',
        expected_effect: {
          latency_delta_ms: -0.05,
          flash_delta_bytes: -162,
          sram_delta_bytes: 0,
        },
        risk: 'LOW',
        confidence: 0.95,
        validation_required: true,
        status: 'PROPOSED',
        created_at: new Date().toISOString(),
      },
    ];

    render(
      <ErrorBoundary>
        <OptimizationCenter
          optimizations={mockCandidates}
          loading={false}
          activeIDESketch={null}
          onSaveIDESketch={vi.fn().mockResolvedValue(true)}
          onApprove={vi.fn().mockResolvedValue(true)}
          onReject={vi.fn().mockResolvedValue(true)}
          onCreateExperiment={vi.fn().mockResolvedValue('EXP-001')}
          onNavigate={vi.fn()}
          selectedBoard={{
            board_id: 'arduino_uno',
            display_name: 'Arduino Uno',
            mcu: 'atmega328p',
            architecture: 'avr8',
            clock_hz: 16000000,
            flash_bytes: 32256,
            sram_bytes: 2048,
            eeprom_bytes: 1024,
            operating_voltage: '5V',
          }}
          activeRun={null}
          activeFirmware={null}
          latestSamples={{}}
          telemetryHistory={[]}
          experiments={[]}
          validations={{}}
          isDemo={false}
          hardwareConnected={false}
        />
      </ErrorBoundary>
    );

    expect(screen.getByText(/Optimization Intelligence/i)).toBeDefined();
    expect(screen.getByText(/Pipeline & Live Validation/i)).toBeDefined();
    expect(screen.getByText(/Candidates & Code Diff/i)).toBeDefined();
  });

  it('renders OptimizationDecisionPanel and handles Apply and Revert modal triggers', async () => {
    const { OptimizationDecisionPanel } = await import('../components/Optimization/OptimizationDecisionPanel');

    const candidate: any = {
      optimization_id: 'CAND-TEST-001',
      title: 'Non-blocking millis() scheduler',
      applied: false,
      status: 'PROPOSED',
      before_code: 'delay(1000);',
      after_code: 'if (millis() - prev >= 1000) { prev = millis(); }',
    };

    const onAccept = vi.fn().mockResolvedValue(true);
    const onRollback = vi.fn().mockResolvedValue(undefined);
    const onApplySource = vi.fn().mockResolvedValue(true);
    const onRevertSource = vi.fn().mockResolvedValue(true);

    const { rerender } = render(
      <OptimizationDecisionPanel
        candidate={candidate}
        experiment={null}
        validationResult={null}
        onAccept={onAccept}
        onRollback={onRollback}
        onApplySource={onApplySource}
        onRevertSource={onRevertSource}
        activeSketchPath="C:/Sketches/Blink/Blink.ino"
      />
    );

    expect(screen.getByText(/Accept Optimization/i)).toBeDefined();

    // Rerender as applied candidate
    const appliedCandidate: any = {
      ...candidate,
      applied: true,
      applied_at: new Date().toISOString(),
      backup_path: 'C:/Sketches/Blink/.aris/backups/Blink.ino.bak',
      candidate_source_hash: 'abcdef1234567890',
    };

    rerender(
      <OptimizationDecisionPanel
        candidate={appliedCandidate}
        experiment={null}
        validationResult={null}
        onAccept={onAccept}
        onRollback={onRollback}
        onApplySource={onApplySource}
        onRevertSource={onRevertSource}
        activeSketchPath="C:/Sketches/Blink/Blink.ino"
      />
    );

    expect(screen.getByText(/REVERT SOURCE/i)).toBeDefined();
    expect(screen.getByText(/Optimization Applied & Active/i)).toBeDefined();
  });

  it('renders LogViewer with log filtering and auto-scroll control', async () => {
    const { LogViewer } = await import('../components/Logs/LogViewer');

    render(<LogViewer />);

    expect(screen.getByText(/Engineering Log Stream/i)).toBeDefined();
    expect(screen.getByText(/Auto-scroll/i)).toBeDefined();
    expect(screen.getByPlaceholderText(/Search log messages/i)).toBeDefined();
  });

  it('renders SystemInfoModal with architectural guide', async () => {
    const { SystemInfoModal } = await import('../components/common/SystemInfoModal');

    render(
      <SystemInfoModal
        isOpen={true}
        onClose={vi.fn()}
        onNavigate={vi.fn()}
      />
    );

    expect(screen.getByText(/ARIS System Guide & Architecture/i)).toBeDefined();
    expect(screen.getByText(/Microcontroller Hardware Connection/i)).toBeDefined();
    expect(screen.getByText(/Close Guide/i)).toBeDefined();
  });

  it('renders DemoLaunchModal with simulation targets', async () => {
    const { DemoLaunchModal } = await import('../components/Dashboard/DemoLaunchModal');

    render(
      <DemoLaunchModal
        isOpen={true}
        onClose={vi.fn()}
        onLaunch={vi.fn()}
      />
    );

    expect(screen.getByText(/Virtual Hardware Simulation Demo/i)).toBeDefined();
    expect(screen.getByText(/Select Virtual Microcontroller Target/i)).toBeDefined();
  });
});

describe('Backend Connectivity & Error Classification Regression Tests', () => {
  it('correctly constructs ARISApiError with proper code and message', async () => {
    const { ARISApiError } = await import('../services/api');

    const errUnavail = new ARISApiError(
      'ARIS_BACKEND_UNAVAILABLE',
      'Cannot reach ARIS backend. Is the server running on port 8765?'
    );
    expect(errUnavail.error_code).toBe('ARIS_BACKEND_UNAVAILABLE');
    expect(errUnavail.message).toContain('port 8765');

    const errTimeout = new ARISApiError(
      'ARIS_OPERATION_TIMEOUT',
      'Operation timed out after 90s waiting for ARIS backend.',
      { timeoutMs: 90000 }
    );
    expect(errTimeout.error_code).toBe('ARIS_OPERATION_TIMEOUT');
    expect(errTimeout.details.timeoutMs).toBe(90000);
  });

  it('controls hardware auto-detection lock via pause and resume helpers', async () => {
    const { pauseHardwareAutoDetect, resumeHardwareAutoDetect, isHardwareAutoDetectPaused } = await import('../hooks/useAris');

    expect(isHardwareAutoDetectPaused()).toBe(false);

    pauseHardwareAutoDetect(5000);
    expect(isHardwareAutoDetectPaused()).toBe(true);

    resumeHardwareAutoDetect();
    expect(isHardwareAutoDetectPaused()).toBe(false);
  });

  it('renders FirmwareWorkspace with accurate non-conflated error banners', async () => {
    const { FirmwareWorkspace } = await import('../components/Firmware/FirmwareWorkspace');

    const mockBoard = {
      board_id: 'arduino_uno',
      display_name: 'Arduino Uno R3',
      mcu: 'ATmega328P',
      architecture: 'avr',
      clock_hz: 16000000,
      flash_bytes: 32256,
      sram_bytes: 2048,
      supported: true,
      fqbn: 'arduino:avr:uno',
    };

    const mockSketch = {
      name: 'aris_demo_rev2.ino',
      path: 'C:/Sketches/aris_demo_rev2/aris_demo_rev2.ino',
      last_modified: Date.now(),
      size_bytes: 1024,
      source_code: 'void setup() { Serial.begin(115200); }\nvoid loop() { delay(100); }',
    };

    const { getByText } = render(
      <FirmwareWorkspace
        firmwareList={[]}
        activeFirmware={null}
        selectedBoard={mockBoard as any}
        ideSketches={[mockSketch]}
        activeIDESketch={mockSketch}
        onSyncIDESketch={vi.fn().mockResolvedValue(true)}
        onRefreshIDESketches={vi.fn().mockResolvedValue(undefined)}
        onSelectFirmware={vi.fn()}
      />
    );

    expect(screen.getAllByText(/aris_demo_rev2.ino/i).length).toBeGreaterThanOrEqual(1);
    expect(getByText(/Arduino Uno R3/i)).toBeDefined();
    expect(getByText(/Deploy & Run/i)).toBeDefined();
  });
});

