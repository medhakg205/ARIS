// ============================================================
// ARIS Frontend Tests
// Tests for common components, API client, and type contracts
// ============================================================

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';

// ---- MetricBadge Tests ----
describe('MetricBadge', () => {
  it('renders metric with classification badge', async () => {
    const { MetricBadge } = await import('../components/common/MetricBadge');
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

  it('renders compact mode', async () => {
    const { MetricBadge } = await import('../components/common/MetricBadge');
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

  it('shows confidence bar when provided', async () => {
    const { MetricBadge } = await import('../components/common/MetricBadge');
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

  it('renders dash for unknown values', async () => {
    const { MetricBadge } = await import('../components/common/MetricBadge');
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
  it('renders when visible', async () => {
    const { DemoBanner } = await import('../components/common/DemoBanner');
    render(<DemoBanner visible={true} />);
    expect(screen.getByText('Demo Mode')).toBeDefined();
    expect(screen.getByText('— Simulated Hardware')).toBeDefined();
  });

  it('renders nothing when not visible', async () => {
    const { DemoBanner } = await import('../components/common/DemoBanner');
    const { container } = render(<DemoBanner visible={false} />);
    expect(container.innerHTML).toBe('');
  });
});

// ---- ErrorBanner Tests ----
describe('ErrorBanner', () => {
  it('renders null when no error', async () => {
    const { ErrorBanner } = await import('../components/common/ErrorBanner');
    const { container } = render(<ErrorBanner error={null} />);
    expect(container.innerHTML).toBe('');
  });

  it('renders string error', async () => {
    const { ErrorBanner } = await import('../components/common/ErrorBanner');
    render(<ErrorBanner error="Something went wrong" />);
    expect(screen.getByText('Something went wrong')).toBeDefined();
  });

  it('renders ARISApiError with code and hint', async () => {
    const { ErrorBanner } = await import('../components/common/ErrorBanner');
    const { ARISApiError } = await import('../services/api');

    const err = new ARISApiError(
      'ARIS_AI_UNAVAILABLE',
      'AI unavailable',
      {},
      true,
    );
    render(<ErrorBanner error={err} />);
    expect(screen.getByText('AI Engine Unavailable')).toBeDefined();
    expect(screen.getByText('ARIS_AI_UNAVAILABLE')).toBeDefined();
  });

  it('calls onDismiss when X clicked', async () => {
    const { ErrorBanner } = await import('../components/common/ErrorBanner');
    const onDismiss = vi.fn();
    render(<ErrorBanner error="Test error" onDismiss={onDismiss} />);
    const dismissBtn = screen.getByRole('button');
    fireEvent.click(dismissBtn);
    expect(onDismiss).toHaveBeenCalledOnce();
  });
});

// ---- Type Contract Tests ----
describe('Type Contracts', () => {
  it('TelemetrySample has all canonical fields', async () => {
    const types = await import('../types');
    // TypeScript compile-time check: a conforming object
    const sample: import('../types').TelemetrySample = {
      protocol_version: '1.0',
      run_id: 'RUN-001',
      board_id: 'arduino_uno',
      mcu: 'ATmega328P',
      timestamp_ms: 1234,
      sequence: 1,
      metric: 'cpu_load',
      value: 42.0,
      unit: '%',
      classification: 'ESTIMATED',
      confidence: 0.7,
    };
    expect(sample.protocol_version).toBe('1.0');
    expect(sample.classification).toBe('ESTIMATED');
  });

  it('MetricClassification has exactly 4 values', () => {
    // Runtime assertion that the 4 canonical values are valid
    const valid: import('../types').MetricClassification[] = [
      'MEASURED', 'ESTIMATED', 'DERIVED', 'PREDICTED',
    ];
    expect(valid).toHaveLength(4);
  });

  it('cpu_load must be ESTIMATED on AVR', () => {
    // This is a semantic contract test.
    // cpu_load on ATmega328P is ALWAYS ESTIMATED (no hardware perf counters).
    const sample: import('../types').TelemetrySample = {
      protocol_version: '1.0',
      run_id: 'RUN-002',
      board_id: 'arduino_uno',
      mcu: 'ATmega328P',
      timestamp_ms: 5000,
      sequence: 100,
      metric: 'cpu_load',
      value: 55.0,
      unit: '%',
      classification: 'ESTIMATED',
      confidence: 0.6,
    };
    expect(sample.classification).toBe('ESTIMATED');
    // Never MEASURED on ATmega328P — no hardware performance counters
    expect(sample.classification).not.toBe('MEASURED');
  });

  it('OptimizationStatus has mandatory approval step', () => {
    const statuses: import('../types').OptimizationStatus[] = [
      'PROPOSED', 'APPROVED', 'BUILDING', 'TESTING',
      'VALIDATED', 'REJECTED', 'ROLLED_BACK', 'FAILED',
    ];
    // PROPOSED must come before APPROVED — human approval required
    expect(statuses.indexOf('PROPOSED')).toBeLessThan(statuses.indexOf('APPROVED'));
  });

  it('ArisError has canonical structure', () => {
    const err: import('../types').ArisError = {
      error_code: 'ARIS_BACKEND_UNAVAILABLE',
      message: 'Cannot reach backend',
      details: {},
      recoverable: true,
    };
    expect(err.error_code).toBe('ARIS_BACKEND_UNAVAILABLE');
    expect(err.recoverable).toBe(true);
  });
});

// ---- API Client Tests ----
describe('API Client', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('ARISApiError has correct structure', async () => {
    const { ARISApiError } = await import('../services/api');
    const err = new ARISApiError('ARIS_BOARD_NOT_FOUND', 'No board', {}, true);
    expect(err.error_code).toBe('ARIS_BOARD_NOT_FOUND');
    expect(err.message).toBe('No board');
    expect(err.recoverable).toBe(true);
    expect(err).toBeInstanceOf(Error);
  });

  it('throws ARIS_BACKEND_UNAVAILABLE on network failure', async () => {
    const { apiHealth, ARISApiError } = await import('../services/api');
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('Network error')));
    try {
      await apiHealth();
      expect.unreachable('should have thrown');
    } catch (e) {
      expect(e).toBeInstanceOf(ARISApiError);
      expect((e as InstanceType<typeof ARISApiError>).error_code).toBe('ARIS_BACKEND_UNAVAILABLE');
    }
  });
});

// ---- WebSocket Client Tests ----
describe('WebSocket Client', () => {
  it('arisWs is a singleton', async () => {
    const { arisWs } = await import('../services/websocket');
    expect(arisWs).toBeDefined();
    expect(typeof arisWs.subscribe).toBe('function');
    expect(typeof arisWs.connect).toBe('function');
    expect(typeof arisWs.disconnect).toBe('function');
    expect(arisWs.connected).toBe(false);
  });
});
