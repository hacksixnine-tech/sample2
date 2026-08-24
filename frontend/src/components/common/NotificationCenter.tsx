import React from 'react';
import {
  X,
  BellRing,
  ShieldAlert,
  AlertTriangle,
  Info,
  CheckCheck,
  Trash2,
  Radio,
  Sparkles,
} from 'lucide-react';
import { useRealtimeEvents, NotificationItem } from '../../context/RealtimeEventContext';

interface NotificationCenterProps {
  isOpen: boolean;
  onClose: () => void;
}

export const NotificationCenter: React.FC<NotificationCenterProps> = ({ isOpen, onClose }) => {
  const {
    notifications,
    unreadCount,
    markAllAsRead,
    clearNotifications,
    sendTestEvent,
    connectionStatus,
  } = useRealtimeEvents();

  if (!isOpen) return null;

  const getSeverityIcon = (sev: string) => {
    switch (sev) {
      case 'CRITICAL':
        return <ShieldAlert className="text-red-400 shrink-0" size={18} />;
      case 'HIGH':
        return <AlertTriangle className="text-amber-400 shrink-0" size={18} />;
      default:
        return <Info className="text-blue-400 shrink-0" size={18} />;
    }
  };

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full max-w-md bg-slate-950/95 backdrop-blur-xl border-l border-slate-800 shadow-2xl flex flex-col transition-all duration-300">
      {/* Header */}
      <div className="p-4 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-blue-500/20 text-blue-400 rounded-lg">
            <BellRing size={18} />
          </div>
          <div>
            <h2 className="font-bold text-white text-base">Real-Time Notification Center</h2>
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <span className="flex items-center gap-1 font-mono">
                <span
                  className={`w-2 h-2 rounded-full ${
                    connectionStatus === 'CONNECTED'
                      ? 'bg-emerald-400 animate-pulse'
                      : connectionStatus === 'RECONNECTING'
                      ? 'bg-amber-400 animate-pulse'
                      : 'bg-red-400'
                  }`}
                />
                {connectionStatus}
              </span>
              <span>•</span>
              <span>{unreadCount} unread</span>
            </div>
          </div>
        </div>

        <button
          onClick={onClose}
          className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition"
          aria-label="Close Notification Center"
        >
          <X size={18} />
        </button>
      </div>

      {/* Action Bar */}
      <div className="px-4 py-2 bg-slate-900/80 border-b border-slate-800/80 flex items-center justify-between text-xs">
        <button
          onClick={markAllAsRead}
          disabled={unreadCount === 0}
          className="text-slate-300 hover:text-white flex items-center gap-1 disabled:opacity-40 transition"
        >
          <CheckCheck size={14} /> Mark All Read
        </button>

        <button
          onClick={clearNotifications}
          disabled={notifications.length === 0}
          className="text-slate-400 hover:text-red-400 flex items-center gap-1 disabled:opacity-40 transition"
        >
          <Trash2 size={14} /> Clear All
        </button>
      </div>

      {/* Notification List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {notifications.length === 0 ? (
          <div className="h-64 flex flex-col items-center justify-center text-center p-6 text-slate-500">
            <BellRing size={32} className="mb-2 opacity-40" />
            <p className="font-semibold text-sm">No live notifications</p>
            <p className="text-xs text-slate-600 mt-1">
              Events and real-time alerts from AI surveillance will appear here automatically.
            </p>
          </div>
        ) : (
          notifications.map((n) => (
            <div
              key={n.id}
              className={`p-3.5 rounded-xl border transition ${
                !n.isRead
                  ? n.severity === 'CRITICAL'
                    ? 'bg-red-950/30 border-red-500/50 shadow-md shadow-red-950/40'
                    : 'bg-slate-900/90 border-blue-500/40'
                  : 'bg-slate-900/40 border-slate-800 text-slate-400'
              }`}
            >
              <div className="flex items-start gap-3">
                {getSeverityIcon(n.severity)}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <h4 className="text-xs font-bold text-white truncate">{n.title}</h4>
                    <span className="text-[10px] font-mono text-slate-400 shrink-0">
                      {new Date(n.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 mt-0.5 leading-relaxed">{n.message}</p>
                  {(n.camera_id || n.district) && (
                    <div className="mt-2 flex items-center gap-2 text-[10px] font-mono text-slate-400">
                      {n.camera_id && <span className="bg-slate-800 px-1.5 py-0.5 rounded text-slate-300">{n.camera_id}</span>}
                      {n.district && <span>{n.district}</span>}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Dev Simulator Trigger Footer */}
      <div className="p-4 border-t border-slate-800 bg-slate-900/60 text-xs">
        <div className="flex items-center justify-between mb-2">
          <span className="text-slate-400 font-semibold flex items-center gap-1">
            <Sparkles size={14} className="text-blue-400" /> Dev Event Simulator:
          </span>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={() => sendTestEvent('WATCHLIST_MATCH', 'CRITICAL')}
            className="px-2.5 py-1.5 bg-red-600/20 hover:bg-red-600/30 border border-red-500/40 text-red-300 rounded-lg text-[11px] font-bold transition flex items-center justify-center gap-1"
          >
            <Radio size={12} /> Watchlist Match
          </button>
          <button
            onClick={() => sendTestEvent('CAMERA_OFFLINE', 'HIGH')}
            className="px-2.5 py-1.5 bg-amber-600/20 hover:bg-amber-600/30 border border-amber-500/40 text-amber-300 rounded-lg text-[11px] font-bold transition flex items-center justify-center gap-1"
          >
            <Radio size={12} /> Camera Offline
          </button>
        </div>
      </div>
    </div>
  );
};
