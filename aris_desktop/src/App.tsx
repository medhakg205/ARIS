// ============================================================
// ARIS Studio — Application Root (v3.0.0-PROFESSIONAL)
// Adaptive Runtime Intelligence System for Embedded Devices
// ============================================================

import React, { useState, useCallback, useEffect } from 'react';
import { useARIS } from './hooks/useAris';
import { useTheme } from './hooks/useTheme';
import { NavTab } from './types/navigation';
import { Sidebar } from './components/Sidebar';
import { TopBar } from './components/TopBar';
import { CommandPalette } from './components/CommandPalette/CommandPalette';
import { GlobalSearchModal } from './components/Search/GlobalSearchModal';
import { NotificationDrawer, type NotificationItem } from './components/Notifications/NotificationDrawer';
import { AboutModal } from './components/About/AboutModal';

// Views
import { OverviewDashboard } from './components/Dashboard/OverviewDashboard';
import { DevicesView } from './components/Devices/DevicesView';
import { FirmwareWorkspace } from './components/Firmware/FirmwareWorkspace';
import { TelemetryLab } from './components/LiveMonitor/TelemetryLab';
import { BaselineCenter } from './components/Baselines/BaselineCenter';
import { OptimizationCenter } from './components/Optimization/OptimizationCenter';
import { ExperimentCenter } from './components/Experiments/ExperimentCenter';
import { AnalysisCenter } from './components/Analysis/AnalysisCenter';
import { ReportCenter } from './components/Reports/ReportCenter';
import { SettingsCenter } from './components/Settings/SettingsCenter';
import { DiagnosticsView } from './components/Diagnostics/DiagnosticsView';
import { LogViewer } from './components/Logs/LogViewer';

// Common
import { ErrorBanner } from './components/common/ErrorBanner';
import { SystemInfoModal } from './components/common/SystemInfoModal';
import { StartupSplash } from './components/Splash/StartupSplash';
import type { FindingRecord, BoardProfile } from './types';

const INITIAL_NOTIFICATIONS: NotificationItem[] = [
  {
    id: 'n-1',
    timestamp: 'Just now',
    type: 'success',
    title: 'ARIS v3.0.0-PROFESSIONAL Ready',
    message: 'Embedded intelligence runtime engine initialized in deterministic mode.',
    read: false,
  },
  {
    id: 'n-2',
    timestamp: '2m ago',
    type: 'info',
    title: 'Hardware Link Standby',
    message: 'pySerial scanner online. 0 physical devices detected. Simulation mode available.',
    read: false,
  },
];

export const App: React.FC = () => {
  const [showSplash, setShowSplash] = useState(() => {
    try {
      return sessionStorage.getItem('aris_splash_shown') !== 'true';
    } catch {
      return true;
    }
  });
  const [activeTab, setActiveTab] = useState<NavTab>('dashboard');
  const [showInfoModal, setShowInfoModal] = useState(false);
  const [showAboutModal, setShowAboutModal] = useState(false);
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const [searchModalOpen, setSearchModalOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [notifications, setNotifications] = useState<NotificationItem[]>(INITIAL_NOTIFICATIONS);

  const aris = useARIS();
  const { themeMode, setThemeMode, toggleTheme } = useTheme();

  const handleSplashComplete = useCallback(() => {
    try {
      sessionStorage.setItem('aris_splash_shown', 'true');
    } catch {}
    setShowSplash(false);
  }, []);

  // Global Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+K or Cmd+K -> Command Palette
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setCommandPaletteOpen((prev) => !prev);
      }
      // Ctrl+Shift+F -> Global Search
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'F') {
        e.preventDefault();
        setSearchModalOpen((prev) => !prev);
      }
      // Ctrl+Shift+P -> Command Palette
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'P') {
        e.preventDefault();
        setCommandPaletteOpen((prev) => !prev);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleNavigate = useCallback((tab: NavTab) => {
    if (tab === 'about') {
      setShowAboutModal(true);
    } else {
      setActiveTab(tab);
    }
  }, []);

  const handleStartDemo = useCallback(async (boardId: string = 'arduino_uno', projectId: string = 'led_blink') => {
    await aris.startDemo(boardId, projectId);
    setActiveTab('telemetry');
  }, [aris]);

  const handleStartHardwareRun = useCallback(async () => {
    await aris.startRun(false);
    setActiveTab('telemetry');
  }, [aris]);

  const handleStopRun = useCallback(async () => {
    await aris.stopRun();
  }, [aris]);

  const handleGenerateCandidate = useCallback(async (finding: FindingRecord) => {
    const fw = aris.activeFirmware;
    let source = fw?.source_code;
    if (!source && aris.activeIDESketch?.source_code) {
      source = aris.activeIDESketch.source_code;
    }
    if (!source) {
      source = 'void setup() {}\nvoid loop() {}';
    }
    await aris.generateCandidate(finding, source);
    setActiveTab('optimize');
  }, [aris]);

  const unreadCount = notifications.filter((n) => !n.read).length;

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-app text-fg select-none relative font-sans">
      {/* Startup Splash Screen */}
      {showSplash && (
        <StartupSplash
          backendOnline={aris.backendOnline}
          hardwareConnected={aris.hardwareConnected}
          selectedBoard={aris.selectedBoard}
          onComplete={handleSplashComplete}
        />
      )}

      {/* Professional Collapsible Sidebar */}
      <Sidebar
        activeTab={activeTab}
        onTabChange={handleNavigate}
        issuesCount={aris.findings.length}
        experimentsCount={aris.experiments.length}
        candidatesCount={aris.optimizations.length}
        hardwareConnected={aris.hardwareConnected}
      />

      {/* Main Workspace Layout */}
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        {/* Top Navigation & Status Bar */}
        <TopBar
          activeTab={activeTab}
          projectName={aris.activeIDESketch?.name || aris.activeFirmware?.name}
          hardwareConnected={aris.hardwareConnected}
          isDemo={aris.isDemo}
          selectedBoard={aris.selectedBoard}
          confidence={aris.isDemo ? 'SIMULATED' : 'PHYSICAL'}
          connectedPort={aris.connectionStatus?.port}
          deviceState={aris.deviceState}
          themeMode={themeMode}
          onThemeChange={setThemeMode}
          onOpenCommandPalette={() => setCommandPaletteOpen(true)}
          onOpenSearch={() => setSearchModalOpen(true)}
          onOpenNotifications={() => setNotificationsOpen(true)}
          onOpenInfo={() => setShowAboutModal(true)}
          onNavigate={handleNavigate}
          unreadNotificationsCount={unreadCount}
          telemetryActive={Boolean(aris.activeRun)}
        />

        {/* Global Error Banner */}
        {aris.lastError && (
          <div className="px-4 pt-2 shrink-0">
            <ErrorBanner error={aris.lastError} onDismiss={aris.clearError} />
          </div>
        )}

        {/* Viewport Center */}
        <main className="flex-1 overflow-hidden relative bg-app">
          {activeTab === 'dashboard' && (
            <OverviewDashboard
              health={aris.health}
              selectedBoard={aris.selectedBoard}
              activeRun={aris.activeRun}
              activeFirmware={aris.activeFirmware}
              activeIDESketch={aris.activeIDESketch}
              hardwareConnected={aris.hardwareConnected}
              isDemo={aris.isDemo}
              latestSamples={aris.latestSamples}
              backendOnline={aris.backendOnline}
              findings={aris.findings}
              optimizations={aris.optimizations}
              onStartDemo={handleStartDemo}
              onStartHardwareRun={handleStartHardwareRun}
              onStopRun={handleStopRun}
              onNavigate={(t: string) => handleNavigate(t as NavTab)}
              onOpenInfo={() => setShowAboutModal(true)}
              connectedPort={aris.connectionStatus?.port}
            />
          )}

          {activeTab === 'devices' && (
            <DevicesView
              boards={aris.boards}
              selectedBoard={aris.selectedBoard}
              onSelectBoard={(b: BoardProfile) => aris.setSelectedBoard(b)}
              connectionStatus={aris.connectionStatus || { connected: false, available_ports: [] }}
              hardwareConnected={aris.hardwareConnected}
              onConnect={async (port: string, baudRate?: number) => {
                try {
                  await aris.connectHardware(port, baudRate);
                  return true;
                } catch {
                  return false;
                }
              }}
              onDisconnect={async () => {
                try {
                  await aris.disconnectHardware();
                  return true;
                } catch {
                  return false;
                }
              }}
              onAutoDetect={async () => {
                try {
                  await aris.autoDetectHardware();
                  return true;
                } catch {
                  return false;
                }
              }}
              isDemo={aris.isDemo}
              onNavigate={(t: string) => handleNavigate(t as NavTab)}
              loading={Boolean(Object.values(aris.loading).some(Boolean))}
            />
          )}

          {activeTab === 'firmware' && (
            <FirmwareWorkspace
              firmwareList={aris.firmwareList}
              activeFirmware={aris.activeFirmware}
              selectedBoard={aris.selectedBoard}
              ideSketches={aris.ideSketches}
              activeIDESketch={aris.activeIDESketch}
              onSyncIDESketch={async (path?: string) => {
                const r = await aris.syncIDESketch(path);
                return Boolean(r);
              }}
              onRefreshIDESketches={aris.refreshIDESketches}
              onSaveIDESketch={aris.saveIDESketch}
              onSelectFirmware={aris.setActiveFirmware}
              onNavigate={(t: string) => handleNavigate(t as NavTab)}
              connectedPort={aris.connectionStatus?.port}
              hardwareConnected={aris.hardwareConnected}
            />
          )}

          {activeTab === 'telemetry' && (
            <TelemetryLab
              activeRun={aris.activeRun}
              wsConnected={aris.wsConnected}
              isDemo={aris.isDemo}
              latestSamples={aris.latestSamples}
              telemetryHistory={Object.values(aris.telemetryHistory).flat()}
              hardwareConnected={aris.hardwareConnected}
              onStartRun={handleStartHardwareRun}
              onStartDemo={handleStartDemo}
              onStopRun={handleStopRun}
              onNavigate={(t: string) => handleNavigate(t as NavTab)}
            />
          )}

          {activeTab === 'baselines' && (
            <BaselineCenter
              selectedBoard={aris.selectedBoard}
              activeRun={aris.activeRun}
              latestSamples={aris.latestSamples}
              onStartBaseline={handleStartHardwareRun}
              onStopBaseline={handleStopRun}
              isDemo={aris.isDemo}
              hardwareConnected={aris.hardwareConnected}
            />
          )}

          {(activeTab === 'optimize' || activeTab === 'optimization') && (
            <OptimizationCenter
              optimizations={aris.optimizations}
              loading={Boolean(Object.values(aris.loading).some(Boolean))}
              activeIDESketch={aris.activeIDESketch}
              onSaveIDESketch={aris.saveIDESketch}
              onApprove={async (id: string) => {
                const r = await aris.approveOptimization(id);
                return Boolean(r);
              }}
              onReject={async (id: string) => {
                const r = await aris.rejectOptimization(id);
                return Boolean(r);
              }}
              onCreateExperiment={async (optId: string) => {
                const exp = await aris.createExperiment(`EXP-${optId.substring(0, 6)}`, optId);
                return exp ? (exp.experiment_id || exp.id || null) : null;
              }}
              onNavigate={(t: string) => handleNavigate(t as NavTab)}
              selectedBoard={aris.selectedBoard}
              activeRun={aris.activeRun}
              activeFirmware={aris.activeFirmware}
              latestSamples={aris.latestSamples}
              telemetryHistory={Object.values(aris.telemetryHistory).flat()}
              experiments={aris.experiments}
              validations={aris.validations}
              isDemo={aris.isDemo}
              hardwareConnected={aris.hardwareConnected}
              onAutoDetectHardware={aris.autoDetectHardware}
              onStartHardwareRun={handleStartHardwareRun}
              onStartDemo={handleStartDemo}
              onValidateExperiment={aris.runExperimentValidation}
              onRollbackExperiment={aris.rollbackExperiment}
              onRollbackOptimization={aris.rollbackOptimization}
            />
          )}

          {activeTab === 'experiments' && (
            <ExperimentCenter
              experiments={aris.experiments}
              optimizations={aris.optimizations}
              onRefresh={async () => {
                await aris.refreshExperiments();
              }}
              onNavigateValidation={() => {
                setActiveTab('reports');
              }}
              onRunExperiment={async (expId: string) => {
                const res = await aris.runExperimentValidation(expId);
                return Boolean(res);
              }}
              loading={Boolean(Object.values(aris.loading).some(Boolean))}
            />
          )}

          {(activeTab === 'analysis' || activeTab === 'issues') && (
            <AnalysisCenter
              findings={aris.findings}
              activeFirmware={aris.activeFirmware}
              activeIDESketch={aris.activeIDESketch}
              onGenerateCandidate={handleGenerateCandidate}
              onNavigate={(t: string) => handleNavigate(t as NavTab)}
              loading={Boolean(aris.loading.findings)}
            />
          )}

          {activeTab === 'reports' && (
            <ReportCenter
              experiments={aris.experiments}
              selectedBoard={aris.selectedBoard}
              patentMarkdown={aris.patentMarkdown}
            />
          )}

          {activeTab === 'settings' && (
            <SettingsCenter
              health={aris.health}
              boards={aris.boards}
              selectedBoard={aris.selectedBoard}
              onSelectBoard={(b: BoardProfile) => aris.setSelectedBoard(b)}
              hardwareConnected={aris.hardwareConnected}
              onConnect={aris.connectHardware}
              onDisconnect={aris.disconnectHardware}
              backendOnline={aris.backendOnline}
            />
          )}

          {activeTab === 'diagnostics' && (
            <DiagnosticsView
              health={aris.health}
              backendOnline={aris.backendOnline}
              hardwareConnected={aris.hardwareConnected}
            />
          )}

          {activeTab === 'logs' && (
            <LogViewer />
          )}
        </main>

        {/* Global Engineering Status Strip */}
        <footer className="h-6 bg-header border-t border-border px-4 flex items-center justify-between text-[11px] font-mono text-muted shrink-0 z-10">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1.5">
              <span className={`w-1.5 h-1.5 rounded-full ${aris.backendOnline ? 'bg-accent-green' : 'bg-accent-red'}`} />
              API: {aris.backendOnline ? 'ONLINE' : 'OFFLINE'}
            </span>
            <span>
              Target: {aris.deviceState === 'CONNECTED' && aris.selectedBoard
                ? aris.selectedBoard.display_name
                : aris.deviceState === 'SIMULATION' && aris.selectedBoard
                ? `${aris.selectedBoard.display_name} (SIMULATION)`
                : '—'}
            </span>
            <span>
              Clock: {aris.selectedBoard
                ? (aris.selectedBoard.clock_hz ? `${aris.selectedBoard.clock_hz / 1e6} MHz` : aris.selectedBoard.clock_mhz ? `${aris.selectedBoard.clock_mhz} MHz` : '—')
                : '—'}
            </span>
            <span>
              SRAM: {aris.selectedBoard
                ? (aris.selectedBoard.sram_bytes ? `${aris.selectedBoard.sram_bytes / 1024} KB` : '—')
                : '—'}
            </span>
            {aris.isDemo && (
              <span className="text-accent-amber font-semibold tracking-wider">SIMULATION STANDBY</span>
            )}
          </div>
          <div className="flex items-center gap-4">
            {aris.activeRun && (
              <span className="text-accent-cyan">
                Run: {aris.activeRun.run_id} ({aris.activeRun.status})
              </span>
            )}
            <span className="text-fg font-semibold">ARIS v3.0.0-PROFESSIONAL</span>
          </div>
        </footer>
      </div>

      {/* Global Modals & Drawers */}
      <CommandPalette
        isOpen={commandPaletteOpen}
        onClose={() => setCommandPaletteOpen(false)}
        onNavigate={handleNavigate}
        onAutoDetect={() => setActiveTab('devices')}
        onCompileFirmware={() => setActiveTab('firmware')}
        onFlashFirmware={() => setActiveTab('firmware')}
        onStartBaseline={() => aris.startRun(false)}
        onStopBaseline={() => aris.stopRun()}
        onToggleTheme={toggleTheme}
        onToggleSidebar={() => {}}
        onGenerateReport={() => setActiveTab('reports')}
      />

      <GlobalSearchModal
        isOpen={searchModalOpen}
        onClose={() => setSearchModalOpen(false)}
        onNavigate={handleNavigate}
        experiments={aris.experiments}
        firmwareList={aris.firmwareList}
        optimizations={aris.optimizations}
        findings={aris.findings}
      />

      <NotificationDrawer
        isOpen={notificationsOpen}
        onClose={() => setNotificationsOpen(false)}
        notifications={notifications}
        onClearAll={() => setNotifications([])}
        onMarkAllAsRead={() =>
          setNotifications((prev) => prev.map((n) => ({ ...n, read: true })))
        }
      />

      <AboutModal
        isOpen={showAboutModal}
        onClose={() => setShowAboutModal(false)}
      />

      <SystemInfoModal
        isOpen={showInfoModal}
        onClose={() => setShowInfoModal(false)}
        onNavigate={(tab) => handleNavigate(tab as NavTab)}
      />
    </div>
  );
};

export default App;
