import React from 'react';
import { useBackendStatus } from '../context/BackendStatusContext';
import { MetricCard } from '../components/common/MetricCard';
import { StatusBadge } from '../components/common/StatusBadge';
import { Server, Database, Activity, ShieldCheck, RefreshCw, Cpu, HardDrive } from 'lucide-react';

export const SystemHealthPage: React.FC = () => {
  const { isConnected, isDbReady, health, readiness, systemInfo, latencyMs, lastChecked, refreshStatus } =
    useBackendStatus();

  return (
    <div className="system-health-page">
      <div className="registry-header-row">
        <div>
          <h2 className="page-title">SYSTEM HEALTH & ARCHITECTURE DIAGNOSTICS</h2>
          <p className="page-subtitle">
            Infrastructure telemetry, PostGIS database connection, latency, and active service modules.
          </p>
        </div>

        <button onClick={refreshStatus} className="btn-primary-action">
          <RefreshCw size={14} />
          <span>RUN DIAGNOSTIC PROBE</span>
        </button>
      </div>

      {/* 4 Health Stat Cards */}
      <div className="metrics-ribbon-grid">
        <MetricCard
          title="FASTAPI SERVICE"
          value={isConnected ? 'HEALTHY' : null}
          icon={Server}
          trend={isConnected ? 'positive' : 'negative'}
          trendLabel={isConnected ? `v${systemInfo?.version || '4.8.0'} [${systemInfo?.environment || 'DEV'}]` : 'OFFLINE'}
        />

        <MetricCard
          title="POSTGRES + POSTGIS"
          value={isDbReady ? 'CONNECTED' : null}
          icon={Database}
          trend={isDbReady ? 'positive' : 'negative'}
          trendLabel={isDbReady ? 'SPATIAL GIST READY' : 'NO DB LINK'}
        />

        <MetricCard
          title="API ROUNDTRIP LATENCY"
          value={latencyMs !== null ? `${latencyMs}ms` : null}
          icon={Activity}
          trend={latencyMs && latencyMs < 50 ? 'positive' : 'warning'}
          trendLabel="MEASURED RTT"
        />

        <MetricCard
          title="ACTIVE MODULES"
          value={systemInfo ? systemInfo.active_modules?.length || 20 : null}
          icon={Cpu}
          trend="neutral"
          trendLabel="REGISTERED SUBSYSTEMS"
        />
      </div>

      {/* Subsystem Health Detail Grid */}
      <div className="health-detail-grid">
        {/* Backend & DB Inspector Card */}
        <div className="glass-panel-card">
          <div className="panel-header">
            <h3 className="panel-title">CORE PLATFORM SERVICES STATUS</h3>
          </div>
          <div className="panel-body">
            <div className="diag-item-row">
              <span className="diag-lbl">Application Name</span>
              <span className="diag-val text-cyan">{systemInfo?.application || 'PHANTOM CCTV Platform'}</span>
            </div>
            <div className="diag-item-row">
              <span className="diag-lbl">Liveness Status</span>
              <StatusBadge status={isConnected ? 'ONLINE' : 'OFFLINE'} />
            </div>
            <div className="diag-item-row">
              <span className="diag-lbl">Readiness & DB Check</span>
              <StatusBadge status={isDbReady ? 'READY' : 'OFFLINE'} />
            </div>
            <div className="diag-item-row">
              <span className="diag-lbl">Last Heartbeat Probe</span>
              <span className="diag-val font-mono text-xs text-muted">
                {lastChecked ? lastChecked.toLocaleTimeString() : 'Awaiting initial probe'}
              </span>
            </div>
          </div>
        </div>

        {/* Enabled Subsystems List */}
        <div className="glass-panel-card">
          <div className="panel-header">
            <h3 className="panel-title">ACTIVE BACKEND MODULES</h3>
          </div>
          <div className="panel-body">
            <div className="modules-chips-wrap">
              {systemInfo?.active_modules && systemInfo.active_modules.length > 0 ? (
                systemInfo.active_modules.map((mod) => (
                  <span key={mod} className="module-chip">
                    <ShieldCheck size={11} className="text-healthy" />
                    <span>{mod}</span>
                  </span>
                ))
              ) : (
                <span className="text-muted text-xs">
                  Modules metadata unavailable while backend is offline.
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
