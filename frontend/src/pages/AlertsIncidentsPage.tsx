import React, { useState, useEffect } from 'react';
import { Alert, Incident } from '../types';
import { alertsApi } from '../api/alerts';
import { incidentsApi } from '../api/incidents';
import { StatusBadge } from '../components/common/StatusBadge';
import { LoadingState, BackendUnavailableState, EmptyState } from '../components/common/LoadingError';
import { useBackendStatus } from '../context/BackendStatusContext';
import { ShieldAlert, FileText, CheckCircle, RefreshCw, Clock, MapPin, Eye } from 'lucide-react';

export const AlertsIncidentsPage: React.FC = () => {
  const { isConnected } = useBackendStatus();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [activeTab, setActiveTab] = useState<'alerts' | 'incidents'>('alerts');
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [alertsRes, incRes] = await Promise.allSettled([
        alertsApi.list({ limit: 50 }),
        incidentsApi.list(),
      ]);

      if (alertsRes.status === 'fulfilled' && alertsRes.value.data) {
        setAlerts(alertsRes.value.data);
      }
      if (incRes.status === 'fulfilled' && incRes.value.data) {
        setIncidents(incRes.value.data);
      }
    } catch {
      // Fallback
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleAcknowledge = async (alertId: string) => {
    try {
      await alertsApi.updateStatus(alertId, 'ACKNOWLEDGED');
      setAlerts((prev) =>
        prev.map((a) => (a.id === alertId ? { ...a, status: 'ACKNOWLEDGED' } : a))
      );
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="alerts-incidents-page">
      <div className="registry-header-row">
        <div>
          <h2 className="page-title">THREAT ALERTS & INCIDENT DOSSIERS</h2>
          <p className="page-subtitle">
            Rule-driven severity classification and multi-camera evidence investigation dossiers.
          </p>
        </div>

        <div className="tab-pill-group">
          <button
            onClick={() => setActiveTab('alerts')}
            className={`tab-btn ${activeTab === 'alerts' ? 'active' : ''}`}
          >
            <ShieldAlert size={14} />
            <span>ACTIVE ALERTS ({alerts.length})</span>
          </button>
          <button
            onClick={() => setActiveTab('incidents')}
            className={`tab-btn ${activeTab === 'incidents' ? 'active' : ''}`}
          >
            <FileText size={14} />
            <span>INVESTIGATION DOSSIERS ({incidents.length})</span>
          </button>
        </div>
      </div>

      <div className="alerts-incidents-body">
        {isLoading ? (
          <LoadingState message="Loading alert state machine & dossiers..." />
        ) : activeTab === 'alerts' ? (
          alerts.length === 0 ? (
            <EmptyState title="No Alerts Pending" message="All threat vectors are nominal." />
          ) : (
            <div className="alerts-table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>ALERT CODE</th>
                    <th>SEVERITY</th>
                    <th>EVENT TYPE</th>
                    <th>CAMERA LOCATION</th>
                    <th>CONFIDENCE</th>
                    <th>STATUS</th>
                    <th>TIME</th>
                    <th>ACTION</th>
                  </tr>
                </thead>
                <tbody>
                  {alerts.map((a) => (
                    <tr key={a.id}>
                      <td className="font-mono text-cyan font-semibold">{a.alert_code}</td>
                      <td>
                        <StatusBadge status={a.severity} />
                      </td>
                      <td className="font-semibold">{a.title}</td>
                      <td>
                        <div className="flex-center-gap">
                          <MapPin size={11} className="text-muted" />
                          <span>{a.location || a.district || 'Zone 07'}</span>
                        </div>
                      </td>
                      <td className="text-healthy font-semibold">{Math.round(a.confidence * 100)}%</td>
                      <td>
                        <StatusBadge status={a.status} />
                      </td>
                      <td className="font-mono text-xs text-muted">
                        {new Date(a.created_at).toLocaleTimeString()}
                      </td>
                      <td>
                        {a.status === 'NEW' && (
                          <button
                            onClick={() => handleAcknowledge(a.id)}
                            className="btn-ack-table"
                            title="Acknowledge Alert"
                          >
                            <CheckCircle size={12} />
                            <span>ACK</span>
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        ) : (
          /* Incidents Tab */
          <div className="incidents-dossier-grid">
            {incidents.length === 0 ? (
              <EmptyState title="No Active Dossiers" message="No formal investigation cases open." />
            ) : (
              incidents.map((inc) => (
                <div key={inc.id} className="dossier-card">
                  <div className="dossier-top">
                    <span className="dossier-num">{inc.incident_number}</span>
                    <StatusBadge status={inc.severity} />
                  </div>
                  <h4 className="dossier-title">{inc.title}</h4>
                  <p className="dossier-summary">{inc.summary}</p>
                  <div className="dossier-footer">
                    <span>{inc.alerts_count} Linked Alerts</span>
                    <span>{inc.evidence_count} SHA-256 Evidences</span>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
};
