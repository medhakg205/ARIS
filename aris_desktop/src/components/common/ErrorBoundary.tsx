import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Terminal } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ARIS Studio caught an unhandled renderer error:', error, errorInfo);
    this.setState({ error, errorInfo });
  }

  private handleReload = () => {
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen w-full bg-[#080A10] text-[#E2E8F0] flex flex-col items-center justify-center p-6 select-none font-sans">
          <div className="max-w-2xl w-full bg-[#0E131F] border border-red-500/30 rounded-xl shadow-2xl p-8 space-y-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400">
                <AlertTriangle size={32} />
              </div>
              <div>
                <h1 className="text-xl font-bold tracking-tight text-white font-mono">
                  ARIS Studio encountered a renderer error
                </h1>
                <p className="text-xs text-slate-400 mt-1 font-mono">
                  The desktop UI caught an unexpected runtime exception during rendering.
                </p>
              </div>
            </div>

            {this.state.error && (
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-xs font-mono text-red-400 font-semibold">
                  <Terminal size={14} />
                  <span>Exception Details:</span>
                </div>
                <div className="p-4 bg-[#05070B] border border-red-500/20 rounded-lg overflow-x-auto text-xs font-mono text-red-300 space-y-2">
                  <div className="font-bold">{this.state.error.name}: {this.state.error.message}</div>
                  {this.state.error.stack && (
                    <pre className="text-[11px] text-slate-400 whitespace-pre-wrap leading-relaxed opacity-80 max-h-48 overflow-y-auto">
                      {this.state.error.stack}
                    </pre>
                  )}
                </div>
              </div>
            )}

            <div className="flex items-center justify-between pt-2 border-t border-slate-800">
              <span className="text-[11px] font-mono text-slate-500">
                ARIS Studio v2.0.0 • Professional Desktop Environment
              </span>
              <button
                onClick={this.handleReload}
                className="flex items-center gap-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-xs font-mono font-bold transition-all shadow-md"
              >
                <RefreshCw size={14} />
                <span>Reload ARIS Studio</span>
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
