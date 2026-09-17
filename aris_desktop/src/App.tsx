// ============================================================
// ARIS — Application Root
// Adaptive Runtime Intelligence System for Embedded Devices
// Engineer 3: AI + Frontend
// ============================================================

import React, { useState, useCallback } from 'react';
import { useARIS } from './hooks/useAris';
import { Navbar, type NavTab } from './components/Navbar';
import { DashboardView } from './components/Dashboard/DashboardView';
import { LiveMonitorView } from './components/LiveMonitor/LiveMonitorView';
import { FirmwareView } from './components/Firmware/FirmwareView';
import { AnalysisView } from './components/Analysis/AnalysisView';
import { OptimizationView } from './components/Optimization/OptimizationView';
import { ExperimentsView } from './components/Experiments/ExperimentsView';
import { ValidationView } from './components/Validation/ValidationView';
import { HistoryView } from './components/History/HistoryView';
import { SettingsView } from './components/Settings/SettingsView';
import { ErrorBanner } from './components/common/ErrorBanner';
import { SystemInfoModal } from './components/common/SystemInfoModal';
import type { FindingRecord } from './types';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavTab>('dashboard');
  const [selectedExperimentId, setSelectedExperimentId] = useState<string | null>(null);
  const [showInfoModal, setShowInfoModal] = useState(false);

  const aris = useARIS();

  const handleNavigate = useCallback((tab: string) => {
    setActiveTab(tab as NavTab);
  }, []);

  const handleStartDemo = useCallback(async () => {
    await aris.startRun(true);
  }, [aris]);

  const handleStartHardwareRun = useCallback(async () => {
    await aris.startRun(false);
    setActiveTab('monitor');
  }, [aris]);

  const handleStopRun = useCallback(async () => {
    await aris.stopRun();
  }, [aris]);

  const handleGenerateCandidate = useCallback(async (finding: FindingRecord) => {
    const fw = aris.activeFirmware;
    const source = fw?.source_code || 'void setup() {}\nvoid loop() {}';
    await aris.generateCandidate(finding, source);
    setActiveTab('optimization');
  }, [aris]);

  const handleNavigateValidation = useCallback((experimentId: string) => {
    setSelectedExperimentId(experimentId);
    setActiveTab('experiments'); // We show validation inline
  }, []);

  return (
    <div className="flex flex-col h-screen w-screen bg-[#181b1f] text-slate-200 overflow-hidden select-none">
      {/* Navigation Header */}
      <Navbar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        hardwareConnected={aris.hardwareConnected}
        wsConnected={aris.wsConnected}
        backendOnline={aris.backendOnline}
        isDemo={aris.isDemo}
        boardName={aris.selectedBoard?.display_name}
        onOpenInfo={() => setShowInfoModal(true)}
      />

      {/* Global Error Banner */}
      {aris.lastError && (
        <div className="px-4 pt-2 shrink-0">
          <ErrorBanner error={aris.lastError} onDismiss={aris.clearError} />
        </div>
      )}

      {/* Main Content */}
      <main className="flex-1 overflow-hidden bg-[#181b1f]">
        {activeTab === 'dashboard' && (
          <DashboardView
            health={aris.health}
            selectedBoard={aris.selectedBoard}
            activeRun={aris.activeRun}
            hardwareConnected={aris.hardwareConnected}
            isDemo={aris.isDemo}
            latestSamples={aris.latestSamples}
            backendOnline={aris.backendOnline}
            onStartDemo={handleStartDemo}
            onStartHardwareRun={handleStartHardwareRun}
            onNavigate={handleNavigate}
            onOpenInfo={() => setShowInfoModal(true)}
          />
        )}

        {activeTab === 'monitor' && (
          <LiveMonitorView
            activeRun={aris.activeRun}
            wsConnected={aris.wsConnected}
            isDemo={aris.isDemo}
            latestSamples={aris.latestSamples}
            telemetryHistory={aris.telemetryHistory}
            hardwareConnected={aris.hardwareConnected}
            onStartRun={handleStartHardwareRun}
          />
        )}

        {activeTab === 'firmware' && (
          <FirmwareView
            firmwareList={aris.firmwareList}
            activeFirmware={aris.activeFirmware}
            selectedBoard={aris.selectedBoard}
            loading={aris.loading}
            lastError={aris.lastError}
            ideSketches={aris.ideSketches}
            activeIDESketch={aris.activeIDESketch}
            onSyncIDESketch={aris.syncIDESketch}
            onRefreshIDESketches={aris.refreshIDESketches}
            onUpload={aris.uploadFirmware}
            onSelectFirmware={aris.setActiveFirmware}
            onClearError={aris.clearError}
          />
        )}

        {activeTab === 'analysis' && (
          <AnalysisView
            findings={aris.findings}
            activeRun={aris.activeRun}
            loading={aris.loading}
            onGenerateCandidate={handleGenerateCandidate}
          />
        )}

        {activeTab === 'optimization' && (
          <OptimizationView
            optimizations={aris.optimizations}
            loading={aris.loading}
            activeIDESketch={aris.activeIDESketch}
            onSaveIDESketch={aris.saveIDESketch}
            onApprove={aris.approveOptimization}
            onReject={aris.rejectOptimization}
            onCreateExperiment={aris.createExperiment}
          />
        )}

        {activeTab === 'experiments' && (
          selectedExperimentId ? (
            <div className="flex flex-col h-full">
              <div className="flex items-center gap-3 px-4 py-2 border-b border-slate-800 shrink-0">
                <button
                  onClick={() => setSelectedExperimentId(null)}
                  className="text-xs font-mono text-slate-400 hover:text-slate-200 transition-colors"
                >
                  ← Back to Experiments
                </button>
              </div>
              <div className="flex-1 overflow-hidden">
                <ValidationView
                  experiments={aris.experiments}
                  validations={aris.validations}
                  selectedExperimentId={selectedExperimentId}
                  onLoadValidation={aris.loadValidation}
                />
              </div>
            </div>
          ) : (
            <ExperimentsView
              experiments={aris.experiments}
              optimizations={aris.optimizations}
              onRefresh={aris.refreshExperiments}
              onNavigateValidation={(id) => setSelectedExperimentId(id)}
            />
          )
        )}

        {activeTab === 'history' && (
          <HistoryView
            experiments={aris.experiments}
            optimizations={aris.optimizations}
            validations={aris.validations}
            onLoadValidation={aris.loadValidation}
            onNavigateValidation={handleNavigateValidation}
          />
        )}

        {activeTab === 'settings' && (
          <SettingsView
            health={aris.health}
            boards={aris.boards}
            selectedBoard={aris.selectedBoard}
            onSelectBoard={aris.setSelectedBoard}
            hardwareConnected={aris.hardwareConnected}
            onConnect={aris.connectHardware}
            onDisconnect={aris.disconnectHardware}
            isDemo={aris.isDemo}
            onStartDemo={handleStartDemo}
            onStopRun={handleStopRun}
            backendOnline={aris.backendOnline}
          />
        )}
      </main>

      {/* Status Bar */}
      <footer className="h-6 bg-[#080a10] border-t border-white/[0.06] px-4 flex items-center justify-between text-[10px] font-mono text-slate-400 shrink-0">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5">
            <span className={`w-1.5 h-1.5 rounded-full ${aris.backendOnline ? 'bg-emerald-400' : 'bg-red-500'}`} />
            Core: {aris.selectedBoard?.architecture?.toUpperCase() || 'AVR8'}
          </span>
          <span>Clock: {aris.selectedBoard ? aris.selectedBoard.clock_hz / 1e6 : 16} MHz</span>
          <span>Flash: {aris.selectedBoard ? aris.selectedBoard.flash_bytes / 1024 : 32} KB</span>
          <span>SRAM: {aris.selectedBoard ? aris.selectedBoard.sram_bytes / 1024 : 2} KB</span>
          {aris.isDemo && (
            <span className="text-amber-400 font-semibold tracking-widest">DEMO MODE</span>
          )}
        </div>
        <div className="flex items-center gap-4">
          {aris.activeRun && (
            <span className="text-slate-500">
              Run: {aris.activeRun.run_id} · {aris.activeRun.status}
            </span>
          )}
          <span className="text-slate-400 font-semibold">ARIS v1.0</span>
        </div>
      </footer>

      {/* System Architecture & Workflow Guide Modal */}
      <SystemInfoModal
        isOpen={showInfoModal}
        onClose={() => setShowInfoModal(false)}
        onNavigate={handleNavigate}
      />
    </div>
  );
};

export default App;
