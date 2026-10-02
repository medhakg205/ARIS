// ============================================================
// ARIS — Notification Drawer Component (v3.0.0)
// Slide-over real-time event log for builds, hardware, baselines
// ============================================================

import React from 'react';
import {
  X,
  Bell,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Info,
  Trash2,
} from 'lucide-react';

export interface NotificationItem {
  id: string;
  timestamp: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  read: boolean;
}

interface NotificationDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  notifications: NotificationItem[];
  onClearAll: () => void;
  onMarkAllAsRead: () => void;
}

export const NotificationDrawer: React.FC<NotificationDrawerProps> = ({
  isOpen,
  onClose,
  notifications,
  onClearAll,
  onMarkAllAsRead,
}) => {
  if (!isOpen) return null;

  const getIcon = (type: NotificationItem['type']) => {
    switch (type) {
      case 'success':
        return <CheckCircle2 size={16} className="text-[var(--accent-green)] shrink-0" />;
      case 'warning':
        return <AlertTriangle size={16} className="text-[var(--accent-amber)] shrink-0" />;
      case 'error':
        return <AlertCircle size={16} className="text-[var(--accent-red)] shrink-0" />;
      default:
        return <Info size={16} className="text-[var(--accent-cyan)] shrink-0" />;
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden select-none">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-xs transition-opacity"
        onClick={onClose}
      />

      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-sm bg-[var(--bg-card)] border-l border-[var(--border-color)] shadow-2xl flex flex-col">
          {/* Header */}
          <div className="h-12 px-4 border-b border-[var(--border-color)] bg-[var(--bg-header)] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bell size={16} className="text-[var(--accent-cyan)]" />
              <span className="font-heading font-bold text-sm text-[var(--text-primary)]">
                Notifications
              </span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[var(--bg-surface)] text-[var(--text-muted)] font-semibold">
                {notifications.length}
              </span>
            </div>

            <div className="flex items-center gap-1">
              {notifications.length > 0 && (
                <button
                  onClick={onClearAll}
                  title="Clear all notifications"
                  className="p-1 rounded text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)] transition-colors"
                >
                  <Trash2 size={14} />
                </button>
              )}
              <button
                onClick={onClose}
                className="p-1 rounded text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)] transition-colors"
              >
                <X size={16} />
              </button>
            </div>
          </div>

          {/* List */}
          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            {notifications.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-6">
                <Bell size={32} className="text-[var(--text-muted)] mb-2 opacity-50" />
                <span className="text-xs font-medium text-[var(--text-primary)]">
                  No notifications yet
                </span>
                <span className="text-[11px] text-[var(--text-muted)] mt-1">
                  Events from builds, hardware connections, and validation tests will appear here.
                </span>
              </div>
            ) : (
              notifications.map((n) => (
                <div
                  key={n.id}
                  className={`p-3 rounded-lg border transition-all ${
                    n.read
                      ? 'bg-[var(--bg-card)] border-[var(--border-color)] text-[var(--text-secondary)]'
                      : 'bg-[var(--bg-surface)] border-[var(--border-hover)] text-[var(--text-primary)] shadow-sm'
                  }`}
                >
                  <div className="flex items-start gap-2.5">
                    {getIcon(n.type)}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-1">
                        <span className="font-semibold text-xs truncate">
                          {n.title}
                        </span>
                        <span className="text-[10px] font-mono text-[var(--text-muted)] shrink-0">
                          {new Date(n.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>
                      <p className="text-[11px] text-[var(--text-muted)] mt-1 leading-relaxed">
                        {n.message}
                      </p>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          {notifications.length > 0 && (
            <div className="p-3 border-t border-[var(--border-color)] bg-[var(--bg-surface)] flex justify-between items-center text-xs">
              <button
                onClick={onMarkAllAsRead}
                className="text-xs font-mono text-[var(--accent-cyan)] hover:underline"
              >
                Mark all as read
              </button>
              <button
                onClick={onClearAll}
                className="text-xs font-mono text-[var(--text-muted)] hover:text-[var(--text-primary)]"
              >
                Clear all
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
