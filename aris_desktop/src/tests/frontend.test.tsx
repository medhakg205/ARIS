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
});
