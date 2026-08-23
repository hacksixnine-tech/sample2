import React, { useState, useEffect } from 'react';
import {
  Activity,
  Database,
  Search,
  Bell,
  LogOut,
  Shield,
  Clock,
  Radio,
  Server,
} from 'lucide-react';
import { useBackendStatus } from '../../context/BackendStatusContext';
import { useAuth } from '../../context/AuthContext';

interface HeaderProps {
  onSearch?: (query: string) => void;
  activeAlertCount?: number;
}

export const Header: React.FC<HeaderProps> = ({ onSearch, activeAlertCount = 0 }) => {
  const { isConnected, isDbReady, latencyMs, systemInfo } = useBackendStatus();
  const { user, operationalMode, logout } = useAuth();
  const [utcTime, setUtcTime] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setUtcTime(now.toUTCString().replace('GMT', 'UTC'));
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (onSearch) onSearch(searchQuery);
  };

  return (
    <header className="top-command-bar" role="banner">
      {/* Left: Brand, Mode & Breadcrumb */}
      <div className="brand-section">
        <div className="logo-badge">
          <Radio className="logo-icon animate-pulse" size={20} />
          <div className="logo-text">
            <span className="logo-title">PHANTOM</span>
            <span className="logo-sub">STATEWIDE CCTV INTEL</span>
          </div>
        </div>

        <div className="op-mode-tag">
          <Shield size={12} className="text-cyan" />
          <span className="mode-label">MODE:</span>
          <span className="mode-val">{operationalMode}</span>
        </div>
      </div>

      {/* Center: Real Backend & DB Status Telemetry */}
      <div className="telemetry-section">
        {/* UTC Precision Time */}
        <div className="clock-badge" title="Coordinated Universal Time">
          <Clock size={13} className="text-cyan" />
          <span className="clock-text">{utcTime || 'UTC SYNCHRONIZING...'}</span>
        </div>

        {/* Backend API Connection Status */}
        <div className={`status-pill ${isConnected ? 'status-online' : 'status-offline'}`}>
          <Server size={13} />
          <div className="pill-meta">
            <span className="pill-title">
              {isConnected ? `API ONLINE (v${systemInfo?.version || '4.8'})` : 'DATA UNAVAILABLE'}
            </span>
            <span className="pill-sub">
              {isConnected && latencyMs !== null ? `${latencyMs}ms LATENCY` : 'BACKEND OFFLINE'}
            </span>
          </div>
        </div>

        {/* Database PostGIS Readiness Status */}
        <div className={`status-pill ${isDbReady ? 'status-db-ready' : 'status-offline'}`}>
          <Database size={13} />
          <div className="pill-meta">
            <span className="pill-title">
              {isDbReady ? 'POSTGIS READY' : 'DATA UNAVAILABLE'}
            </span>
            <span className="pill-sub">
              {isDbReady ? 'SPATIAL INDEXED' : 'DB DISCONNECTED'}
            </span>
          </div>
        </div>
      </div>

      {/* Right: Global Search, Alerts & Operator Profile */}
      <div className="actions-section">
        {/* Global Search */}
        <form onSubmit={handleSearchSubmit} className="global-search-box">
          <Search size={14} className="search-icon" />
          <input
            type="text"
            placeholder="Search cameras, plates, incidents (Ctrl+K)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            aria-label="Global Surveillance Search"
          />
          <kbd className="search-kbd">Ctrl+K</kbd>
        </form>

        {/* Notifications & Active Alert Counter */}
        <button className="icon-btn" title="Active Alerts Queue" aria-label="Alerts Queue">
          <Bell size={16} />
          {activeAlertCount > 0 && (
            <span className="alert-count-bubble">{activeAlertCount}</span>
          )}
        </button>

        {/* User Profile & RBAC */}
        <div className="user-profile-badge">
          <div className="user-avatar">{user.full_name.substring(0, 2).toUpperCase()}</div>
          <div className="user-meta">
            <span className="user-name">{user.full_name}</span>
            <span className="user-role">{user.role}</span>
          </div>
        </div>

        {/* Logout Action */}
        <button
          onClick={logout}
          className="icon-btn text-danger"
          title="Lock / Logout Station"
          aria-label="Logout"
        >
          <LogOut size={16} />
        </button>
      </div>
    </header>
  );
};
