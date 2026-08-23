import React from 'react';
import { Alert } from '../../types';
import { StatusBadge } from '../common/StatusBadge';
import { LoadingState, EmptyState, BackendUnavailableState } from '../common/LoadingError';
import { ShieldAlert, CheckCircle, Clock, MapPin, BellRing } from 'lucide-react';

interface AlertPanelProps {
  alerts: Alert[];
  isLoading: boolean;
  isBackendUnavailable: boolean;
  onAcknowledge?: (alertId: string) => void;
  onSelectAlert?: (alert: Alert) => void;
  onRetry?: () => void;
}

export const AlertPanel: React.FC<AlertPanelProps> = ({
  alerts,
  isLoading,
  isBackendUnavailable,
  onAcknowledge,
  onSelectAlert,
  onRetry,
}) => {
  return (
    <div className="alert-panel-card">
      <div className="panel-header">
        <div className="panel-title-group">
          <ShieldAlert size={16} className="text-warning" />
          <h3 className="panel-title">REAL-TIME THREAT ALERTS</h3>
        </div>
        <span className="alert-count-pill">{alerts.length} ACTIVE</span>
      </div>

      <div className="alert-feed-list">
        {isLoading ? (
          <LoadingState message="Loading threat alert queue..." />
        ) : isBackendUnavailable ? (
          <BackendUnavailableState endpointName="Alert Engine" onRetry={onRetry} />
        ) : alerts.length === 0 ? (
          <EmptyState title="No Active Alerts" message="Statewide threat detection nominal. No pending incidents." />
        ) : (
          alerts.map((alert) => (
            <div
              key={alert.id}
              className={`alert-item-card severity-${alert.severity.toLowerCase()}`}
              onClick={() => onSelectAlert && onSelectAlert(alert)}
            >
              <div className="alert-item-top">
                <StatusBadge status={alert.severity} />
                <span className="alert-code">{alert.alert_code}</span>
                <span className="alert-time">
                  <Clock size={11} />
                  {new Date(alert.created_at).toLocaleTimeString()}
                </span>
              </div>

              <div className="alert-item-body">
                <h4 className="alert-item-title">{alert.title}</h4>
                {alert.description && (
                  <p className="alert-item-desc">{alert.description}</p>
                )}
              </div>

              <div className="alert-item-footer">
                <div className="alert-meta-col">
                  {alert.location && (
                    <span className="meta-loc">
                      <MapPin size={11} />
                      {alert.location}
                    </span>
                  )}
                  <span className="meta-conf">
                    {Math.round(alert.confidence * 100)}% CONFIDENCE
                  </span>
                </div>

                {alert.status === 'NEW' && onAcknowledge && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onAcknowledge(alert.id);
                    }}
                    className="btn-ack-alert"
                    title="Acknowledge Alert"
                  >
                    <CheckCircle size={12} />
                    <span>ACKNOWLEDGE</span>
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
