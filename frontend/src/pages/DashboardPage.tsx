import React, { useState, useEffect } from 'react';
import { Camera, Alert, CameraCoverage } from '../types';
import { camerasApi } from '../api/cameras';
import { alertsApi } from '../api/alerts';
import { MetricCard } from '../components/common/MetricCard';
import { CameraCard } from '../components/camera/CameraCard';
import { AlertPanel } from '../components/alerts/AlertPanel';
import { LoadingState } from '../components/common/LoadingError';
import { useBackendStatus } from '../context/BackendStatusContext';
import { useRealtimeEvents } from '../context/RealtimeEventContext';
import {
  Camera as CamIcon,
  Wifi,
  WifiOff,
  BellRing,
  Car,
  ListOrdered,
  Compass,
  Cpu,
  RefreshCw,
  Grid,
  Filter,
  Layers,
} from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const { isConnected } = useBackendStatus();
  const { latestEvent, connectionStatus } = useRealtimeEvents();
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [coverage, setCoverage] = useState<CameraCoverage | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [selectedDistrict, setSelectedDistrict] = useState<string>('ALL');
  const [selectedCamera, setSelectedCamera] = useState<Camera | null>(null);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [anprCount, setAnprCount] = useState<number>(1420);
  const [watchlistMatchCount, setWatchlistMatchCount] = useState<number>(12);

  // Real-time Event Listener & State Synchronization
  useEffect(() => {
    if (!latestEvent) return;

    const evtType = latestEvent.event_type;
    const payload = latestEvent.payload || {};

    if (evtType === 'ALERT_CREATED' || evtType === 'WATCHLIST_MATCH') {
      const newAlert: Alert = {
        id: latestEvent.event_id,
        alert_code: payload.alert_code || `ALT-${latestEvent.event_id.substring(0, 8).toUpperCase()}`,
        title: payload.title || `Real-Time Alert: ${latestEvent.entity_id || 'Vehicle'}`,
        description: payload.message || payload.description || 'Live AI detection match.',
        severity: (latestEvent.severity as any) || 'CRITICAL',
        status: 'NEW',
        event_type: evtType,
        camera_id: latestEvent.camera_id,
        camera_name: payload.camera_name || latestEvent.camera_id,
        district: latestEvent.district,
        confidence: payload.confidence || 0.98,
        entity_id: latestEvent.entity_id,
        created_at: latestEvent.timestamp,
      };

      setAlerts((prev) => [newAlert, ...prev.filter((a) => a.id !== newAlert.id)]);
      if (evtType === 'WATCHLIST_MATCH') {
        setWatchlistMatchCount((c) => c + 1);
      }
    } else if (evtType === 'ALERT_ACKNOWLEDGED') {
      const alertId = payload.alert_id || latestEvent.entity_id;
      if (alertId) {
        setAlerts((prev) =>
          prev.map((a) => (a.id === alertId ? { ...a, status: 'ACKNOWLEDGED' } : a))
        );
      }
    } else if (evtType === 'ALERT_RESOLVED' || evtType === 'ALERT_DISMISSED') {
      const alertId = payload.alert_id || latestEvent.entity_id;
      const targetStatus = evtType === 'ALERT_RESOLVED' ? 'RESOLVED' : 'DISMISSED';
      if (alertId) {
        setAlerts((prev) =>
          prev.map((a) => (a.id === alertId ? { ...a, status: targetStatus as any } : a))
        );
      }
    } else if (evtType === 'ANPR_DETECTED' || evtType === 'VEHICLE_DETECTED') {
      setAnprCount((c) => c + 1);
    } else if (evtType === 'CAMERA_OFFLINE') {
      const camId = latestEvent.camera_id;
      setCameras((prev) =>
        prev.map((c) => (c.id === camId || c.camera_code === camId ? { ...c, status: 'OFFLINE' } : c))
      );
      setCoverage((prev) =>
        prev
          ? {
              ...prev,
              operational_cameras: Math.max(0, prev.operational_cameras - 1),
              offline_cameras: prev.offline_cameras + 1,
            }
          : null
      );
    } else if (evtType === 'CAMERA_ONLINE') {
      const camId = latestEvent.camera_id;
      setCameras((prev) =>
        prev.map((c) => (c.id === camId || c.camera_code === camId ? { ...c, status: 'ONLINE' } : c))
      );
      setCoverage((prev) =>
        prev
          ? {
              ...prev,
              operational_cameras: prev.operational_cameras + 1,
              offline_cameras: Math.max(0, prev.offline_cameras - 1),
            }
          : null
      );
    }
  }, [latestEvent]);

  const fetchDashboardData = async () => {
    setIsLoading(true);
    try {
      // 1. Fetch live cameras from backend or fallback to direct corp8 catalog
      let loadedCams: Camera[] = [];
      try {
        const res = await camerasApi.list({ page_size: 30 });
        if (res && res.data && res.data.length > 0) {
          loadedCams = res.data;
        }
      } catch {
        // Fallback
      }

      if (loadedCams.length === 0) {
        loadedCams = await camerasApi.fetchDirectCorp8Catalog();
      }

      setCameras(loadedCams);

      // 2. Fetch coverage and alerts
      const [covRes, alertsRes] = await Promise.allSettled([
        camerasApi.getCoverage(),
        alertsApi.list({ limit: 10 }),
      ]);

      if (covRes.status === 'fulfilled' && covRes.value.data) {
        setCoverage(covRes.value.data);
      } else {
        setCoverage({
          total_cameras: loadedCams.length,
          operational_cameras: loadedCams.filter((c) => c.status === 'ONLINE').length,
          offline_cameras: loadedCams.filter((c) => c.status === 'OFFLINE').length,
          maintenance_cameras: 0,
          departments_count: 5,
          districts_count: 8,
          by_department: {},
          by_district: {},
        });
      }

      if (alertsRes.status === 'fulfilled' && alertsRes.value.data) {
        setAlerts(alertsRes.value.data);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleSyncSource = async () => {
    setIsSyncing(true);
    try {
      await camerasApi.syncExternalCameras();
      await fetchDashboardData();
    } catch {
      await fetchDashboardData();
    } finally {
      setIsSyncing(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const handleAcknowledgeAlert = async (alertId: string) => {
    try {
      await alertsApi.updateStatus(alertId, 'ACKNOWLEDGED');
      setAlerts((prev) =>
        prev.map((a) => (a.id === alertId ? { ...a, status: 'ACKNOWLEDGED' } : a))
      );
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    }
  };

  const districts = Array.from(new Set(cameras.map((c) => c.district).filter(Boolean)));

  const filteredCameras = cameras.filter((c) => {
    if (selectedDistrict !== 'ALL' && c.district !== selectedDistrict) return false;
    return true;
  });

  // Display initial 4 cameras for the dashboard CCTV quad matrix
  const displayQuad = filteredCameras.slice(0, 4);

  return (
    <div className="dashboard-page-container">
      {/* 8-Card Telemetry Ribbon */}
      <section className="metrics-ribbon-grid" aria-label="Key Platform Metrics">
        <MetricCard
          title="TOTAL CAMERAS"
          value={coverage?.total_cameras || cameras.length}
          icon={CamIcon}
          trend="neutral"
          trendLabel={`${districts.length || 8} DISTRICTS ACTIVE`}
          isLoading={isLoading}
        />

        <MetricCard
          title="ONLINE CAMERAS"
          value={coverage?.operational_cameras || cameras.length}
          icon={Wifi}
          trend="positive"
          trendLabel="LIVE CCTV INGEST"
          isLoading={isLoading}
        />

        <MetricCard
          title="OFFLINE CAMERAS"
          value={coverage?.offline_cameras || 0}
          icon={WifiOff}
          trend={coverage?.offline_cameras && coverage.offline_cameras > 0 ? 'warning' : 'positive'}
          trendLabel="NODE DISCONNECT"
          isLoading={isLoading}
        />

        <MetricCard
          title="ACTIVE ALERTS"
          value={alerts.length > 0 ? alerts.length : 0}
          icon={BellRing}
          trend={alerts.length > 0 ? 'negative' : 'positive'}
          trendLabel={alerts.length > 0 ? 'DEFCON 3 ELEVATED' : 'STATEWIDE CLEAR'}
          isLoading={isLoading}
        />

        <MetricCard
          title="ANPR DETECTIONS"
          value="1,420"
          subValue="/hr"
          icon={Car}
          trend="neutral"
          trendLabel="GUJARAT RTO OCR"
          isLoading={isLoading}
        />

        <MetricCard
          title="WATCHLIST MATCHES"
          value="12"
          icon={ListOrdered}
          trend="warning"
          trendLabel="STOLEN & SUSPECT"
          isLoading={isLoading}
        />

        <MetricCard
          title="ACTIVE INVESTIGATIONS"
          value="08"
          icon={Compass}
          trend="neutral"
          trendLabel="TRAJECTORY DOSSIERS"
          isLoading={isLoading}
        />

        <MetricCard
          title="AI PROCESSING STATUS"
          value="4.2ms"
          subValue="AVG"
          icon={Cpu}
          trend="positive"
          trendLabel="INFERENCE NOMINAL"
          isLoading={isLoading}
        />
      </section>

      {/* Main Command Canvas Layout */}
      <div className="dashboard-canvas-layout">
        {/* Left: 4-Camera Live Surveillance Wall */}
        <section className="cctv-wall-section">
          <div className="section-toolbar">
            <div className="toolbar-title-group">
              <Grid size={15} className="text-cyan" />
              <h2 className="section-heading">STATEWIDE CCTV WALL (LIVE 4-QUAD MATRIX)</h2>
            </div>

            <div className="toolbar-actions-group">
              <div className="district-filter-select">
                <Filter size={12} className="text-cyan" />
                <select
                  value={selectedDistrict}
                  onChange={(e) => setSelectedDistrict(e.target.value)}
                  className="registry-select"
                >
                  <option value="ALL">ALL DISTRICTS ({cameras.length})</option>
                  {districts.map((d) => (
                    <option key={d} value={d}>
                      {d}
                    </option>
                  ))}
                </select>
              </div>

              <button
                onClick={handleSyncSource}
                className="btn-toolbar-refresh"
                title="Sync from live.corp8.cloud"
                disabled={isSyncing}
              >
                <Layers size={13} className={isSyncing ? 'animate-spin' : ''} />
                <span>{isSyncing ? 'SYNCING...' : 'SYNC CORP8'}</span>
              </button>

              <button
                onClick={fetchDashboardData}
                className="btn-toolbar-refresh"
                title="Refresh Camera Ingest"
              >
                <RefreshCw size={13} className={isLoading ? 'animate-spin' : ''} />
                <span>REFRESH</span>
              </button>
            </div>
          </div>

          {isLoading ? (
            <LoadingState message="Connecting to live HLS/WebRTC streaming nodes from live.corp8.cloud..." />
          ) : (
            <div className="cctv-quad-container">
              {displayQuad.map((cam) => (
                <CameraCard
                  key={cam.id}
                  camera={cam}
                  isFocused={selectedCamera?.id === cam.id}
                  onSelect={setSelectedCamera}
                />
              ))}
            </div>
          )}
        </section>

        {/* Right: Live Real-Time Threat Alerts Panel */}
        <aside className="dashboard-side-panel">
          <AlertPanel
            alerts={alerts}
            isLoading={isLoading}
            isBackendUnavailable={false}
            onAcknowledge={handleAcknowledgeAlert}
            onRetry={fetchDashboardData}
          />
        </aside>
      </div>
    </div>
  );
};
