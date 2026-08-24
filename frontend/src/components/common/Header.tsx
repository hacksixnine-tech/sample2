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
  Volume2,
  VolumeX,
  Sun,
  Moon,
  Menu,
  X,
} from 'lucide-react';
import { useBackendStatus } from '../../context/BackendStatusContext';
import { useAuth } from '../../context/AuthContext';
import { useRealtimeEvents } from '../../context/RealtimeEventContext';
import { useTheme } from '../../context/ThemeContext';
import { NotificationCenter } from './NotificationCenter';

interface HeaderProps {
  onSearch?: (query: string) => void;
  activeAlertCount?: number;
  isMobileMenuOpen?: boolean;
  onToggleMobileMenu?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  onSearch,
  activeAlertCount = 0,
  isMobileMenuOpen = false,
  onToggleMobileMenu,
}) => {
  const { theme, toggleTheme } = useTheme();
  const { isConnected, isDbReady, latencyMs, systemInfo } = useBackendStatus();
  const { connectionStatus, unreadCount, isSoundEnabled, toggleSound } = useRealtimeEvents();
  const { user, operationalMode, logout } = useAuth();
  const [utcTime, setUtcTime] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [isNotifOpen, setIsNotifOpen] = useState<boolean>(false);
  const [isSearchOpenMobile, setIsSearchOpenMobile] = useState<boolean>(false);

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
    setIsSearchOpenMobile(false);
  };

  return (
    <>
      <header className="top-command-bar" role="banner">
        {/* Left: Hamburger (Mobile), Brand, Mode */}
        <div className="brand-section">
          {onToggleMobileMenu && (
            <button
              onClick={onToggleMobileMenu}
              className="mobile-nav-toggle-btn"
              aria-label={isMobileMenuOpen ? 'Close Navigation Menu' : 'Open Navigation Menu'}
              title="Toggle Menu"
            >
              {isMobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          )}

          <div className="logo-badge">
            <Radio className="logo-icon animate-pulse" size={20} />
            <div className="logo-text">
              <span className="logo-title">PHANTOM</span>
              <span className="logo-sub">STATEWIDE CCTV INTEL</span>
            </div>
          </div>

          <div className="op-mode-tag hide-on-mobile">
            <Shield size={12} className="text-cyan" />
            <span className="mode-label">MODE:</span>
            <span className="mode-val">{operationalMode}</span>
          </div>
        </div>

        {/* Center: Telemetry (Responsive - hides detailed stats on small screens) */}
        <div className="telemetry-section hide-on-tablet">
          {/* UTC Precision Time */}
          <div className="clock-badge" title="Coordinated Universal Time">
            <Clock size={13} className="text-cyan" />
            <span className="clock-text">{utcTime || 'UTC SYNCHRONIZING...'}</span>
          </div>

          {/* Real-time WebSocket Status */}
          <div
            className={`status-pill ${
              connectionStatus === 'CONNECTED'
                ? 'status-online'
                : connectionStatus === 'RECONNECTING'
                ? 'status-warning'
                : 'status-offline'
            }`}
            title="Real-Time Event WebSocket Feed"
          >
            <Radio size={13} className={connectionStatus === 'CONNECTED' ? 'animate-pulse text-emerald-400' : ''} />
            <div className="pill-meta">
              <span className="pill-title">
                {connectionStatus === 'CONNECTED'
                  ? 'LIVE WEBSOCKET'
                  : connectionStatus === 'RECONNECTING'
                  ? 'RECONNECTING WS'
                  : 'WS OFFLINE'}
              </span>
              <span className="pill-sub">
                {connectionStatus === 'CONNECTED' ? 'REAL-TIME STREAM' : 'POLLING BACKEND'}
              </span>
            </div>
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

        {/* Right: Theme Toggle, Search, Sound, Notifications & Operator Profile */}
        <div className="actions-section">
          {/* Global Search Box (Desktop/Laptop) */}
          <form onSubmit={handleSearchSubmit} className="global-search-box hide-on-mobile">
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

          {/* Mobile Search Button */}
          <button
            onClick={() => setIsSearchOpenMobile(!isSearchOpenMobile)}
            className="icon-btn show-on-mobile"
            title="Search"
            aria-label="Search"
          >
            <Search size={16} />
          </button>

          {/* 🌟 Theme Switcher: Light / Dark Mode */}
          <button
            onClick={toggleTheme}
            className="icon-btn theme-toggle-btn"
            title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            aria-label="Toggle Theme Mode"
          >
            {theme === 'dark' ? (
              <Sun size={17} className="theme-icon sun-icon text-amber-400" />
            ) : (
              <Moon size={17} className="theme-icon moon-icon text-indigo-600" />
            )}
          </button>

          {/* Tactical Sound Toggle */}
          <button
            onClick={toggleSound}
            className={`icon-btn hide-on-mobile ${isSoundEnabled ? 'text-cyan' : 'text-muted'}`}
            title={isSoundEnabled ? 'Sound Notifications ON' : 'Sound Notifications MUTED'}
            aria-label="Toggle Sound Notifications"
          >
            {isSoundEnabled ? <Volume2 size={16} /> : <VolumeX size={16} />}
          </button>

          {/* Notification Center Trigger */}
          <button
            onClick={() => setIsNotifOpen(true)}
            className="icon-btn relative"
            title="Real-Time Notification Drawer"
            aria-label="Notification Center"
          >
            <Bell size={16} />
            {(unreadCount > 0 || activeAlertCount > 0) && (
              <span className="alert-count-bubble animate-pulse">
                {unreadCount > 0 ? unreadCount : activeAlertCount}
              </span>
            )}
          </button>

          {/* User Profile & RBAC */}
          <div className="user-profile-badge">
            <div className="user-avatar">{user.full_name.substring(0, 2).toUpperCase()}</div>
            <div className="user-meta hide-on-mobile">
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

      {/* Mobile Search Overlay Input */}
      {isSearchOpenMobile && (
        <div className="mobile-search-bar">
          <form onSubmit={handleSearchSubmit} className="mobile-search-form">
            <Search size={16} className="search-icon" />
            <input
              type="text"
              placeholder="Search cameras, plates, incidents..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              autoFocus
            />
            <button
              type="button"
              className="icon-btn"
              onClick={() => setIsSearchOpenMobile(false)}
            >
              <X size={16} />
            </button>
          </form>
        </div>
      )}

      {/* Notification Center Drawer */}
      <NotificationCenter isOpen={isNotifOpen} onClose={() => setIsNotifOpen(false)} />
    </>
  );
};
