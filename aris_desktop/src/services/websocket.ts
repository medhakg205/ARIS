// ============================================================
// ARIS WebSocket Client
// Connects to /ws/telemetry/{run_id} (canonical contract)
// Resilient: auto-reconnect with exponential backoff
// ============================================================

import type { TelemetrySample, RunRecord, ArisError } from '../types';

export type WsMessage =
  | { type: 'TELEMETRY_UPDATE'; data: TelemetrySample; source: string }
  | { type: 'RUN_STATUS'; data: RunRecord; source: string }
  | { type: 'ERROR'; data: ArisError; source: string }
  | { type: 'CONNECTION_STATE'; connected: boolean; reason?: string };

type MessageHandler = (msg: WsMessage) => void;

const WS_BASE = 'ws://127.0.0.1:8765';
const MAX_RECONNECT_DELAY_MS = 8000;
const INITIAL_RECONNECT_DELAY_MS = 500;

export class ARISWebSocket {
  private ws: WebSocket | null = null;
  private handlers: Set<MessageHandler> = new Set();
  private reconnectDelay = INITIAL_RECONNECT_DELAY_MS;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private shouldReconnect = false;
  private currentRunId: string | null = null;
  private sequenceBuffer: number[] = [];

  constructor() {}

  connect(runId?: string | null): void {
    this.shouldReconnect = true;
    this.currentRunId = runId ?? null;
    this._openSocket();
  }

  disconnect(): void {
    this.shouldReconnect = false;
    this.currentRunId = null;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
    this._emit({ type: 'CONNECTION_STATE', connected: false, reason: 'Disconnected by user' });
  }

  subscribe(handler: MessageHandler): () => void {
    this.handlers.add(handler);
    return () => this.handlers.delete(handler);
  }

  get connected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  private _openSocket(): void {
    const path = this.currentRunId
      ? `/ws/telemetry/${this.currentRunId}`
      : '/ws/telemetry';
    const url = `${WS_BASE}${path}`;

    try {
      this.ws = new WebSocket(url);
    } catch {
      this._scheduleReconnect('Failed to create WebSocket');
      return;
    }

    this.ws.onopen = () => {
      this.reconnectDelay = INITIAL_RECONNECT_DELAY_MS;
      this._emit({ type: 'CONNECTION_STATE', connected: true });
    };

    this.ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data as string) as WsMessage;
        // Track sequence for out-of-order detection
        if (msg.type === 'TELEMETRY_UPDATE') {
          const sample = msg.data as TelemetrySample;
          this.sequenceBuffer.push(sample.sequence);
          if (this.sequenceBuffer.length > 500) {
            this.sequenceBuffer.shift();
          }
        }
        this._emit(msg);
      } catch {
        // Malformed frame - emit ARIS_TELEMETRY_INVALID
        this._emit({
          type: 'ERROR',
          data: {
            error_code: 'ARIS_TELEMETRY_INVALID',
            message: 'Received malformed telemetry frame from backend.',
            details: { raw: event.data },
            recoverable: true,
          },
          source: 'SYSTEM',
        });
      }
    };

    this.ws.onerror = () => {
      // Deliberately minimal — onerror is always followed by onclose
    };

    this.ws.onclose = (event) => {
      this.ws = null;
      this._emit({
        type: 'CONNECTION_STATE',
        connected: false,
        reason: event.reason || `WebSocket closed (code ${event.code})`,
      });
      if (this.shouldReconnect) {
        this._scheduleReconnect('WebSocket closed');
      }
    };
  }

  private _scheduleReconnect(reason: string): void {
    if (this.reconnectTimer) return;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      if (this.shouldReconnect) {
        this._openSocket();
      }
    }, this.reconnectDelay);
    this.reconnectDelay = Math.min(this.reconnectDelay * 2, MAX_RECONNECT_DELAY_MS);
  }

  private _emit(msg: WsMessage): void {
    this.handlers.forEach((h) => {
      try { h(msg); } catch { /* isolate handler errors */ }
    });
  }
}

// Singleton instance
export const arisWs = new ARISWebSocket();
