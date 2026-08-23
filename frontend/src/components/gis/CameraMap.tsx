import React, { useEffect, useRef, useState, useMemo } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Camera } from '../../types';
import {
  Compass,
  Layers,
  Filter,
  Eye,
  Radio,
  RefreshCw,
  Maximize2,
  AlertTriangle,
  LocateFixed,
  Route,
  Activity,
  Shield,
  Zap,
} from 'lucide-react';
import { StatusBadge } from '../common/StatusBadge';
import { CameraPlayer } from '../camera/CameraPlayer';

interface CameraMapProps {
  cameras: Camera[];
  selectedCamera: Camera | null;
  onSelectCamera: (camera: Camera | null) => void;
  isLoading?: boolean;
  corridorPoints?: { start_lat: number; start_lon: number; end_lat: number; end_lon: number } | null;
  onRadiusProbe?: (lat: number, lon: number, radiusMeters: number) => void;
}

// Gujarat State Geographic Bounding Bounds
const GUJARAT_CENTER: [number, number] = [22.4, 71.8];
const DEFAULT_ZOOM = 7.5;

export const CameraMap: React.FC<CameraMapProps> = ({
  cameras,
  selectedCamera,
  onSelectCamera,
  isLoading = false,
  corridorPoints,
  onRadiusProbe,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markersLayerRef = useRef<L.LayerGroup | null>(null);
  const coverageLayerRef = useRef<L.LayerGroup | null>(null);
  const corridorLayerRef = useRef<L.LayerGroup | null>(null);

  // Ref to always access the latest setLiveStreamModalCam from Leaflet event handlers
  const openLiveStreamRef = useRef<(cam: Camera) => void>(() => {});
  openLiveStreamRef.current = (cam: Camera) => setLiveStreamModalCam(cam);

  const [districtFilter, setDistrictFilter] = useState<string>('ALL');
  const [departmentFilter, setDepartmentFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [showCoverageCircles, setShowCoverageCircles] = useState<boolean>(true);
  const [liveStreamModalCam, setLiveStreamModalCam] = useState<Camera | null>(null);
  const [probeRadius, setProbeRadius] = useState<number>(5000);
  const [isProbing, setIsProbing] = useState<boolean>(false);

  // Extract unique district and department lists
  const districts = useMemo(() => {
    return Array.from(new Set(cameras.map((c) => c.district).filter(Boolean))).sort();
  }, [cameras]);

  const departments = useMemo(() => {
    return Array.from(new Set(cameras.map((c) => c.department_name).filter(Boolean))).sort();
  }, [cameras]);

  // Filter cameras
  const filteredCameras = useMemo(() => {
    return cameras.filter((cam) => {
      if (districtFilter !== 'ALL' && cam.district !== districtFilter) return false;
      if (departmentFilter !== 'ALL' && cam.department_name !== departmentFilter) return false;
      if (statusFilter !== 'ALL' && cam.status !== statusFilter) return false;
      return true;
    });
  }, [cameras, districtFilter, departmentFilter, statusFilter]);

  // 1. Initialize Leaflet Map
  useEffect(() => {
    if (!mapContainerRef.current) return;
    if (mapInstanceRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: GUJARAT_CENTER,
      zoom: DEFAULT_ZOOM,
      minZoom: 6,
      maxZoom: 18,
      zoomControl: false,
      attributionControl: false,
    });

    // Dark Matter Tactical CartoDB Tiles with OpenStreetMap fallback
    L.tileLayer(
      'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
      {
        subdomains: 'abcd',
        maxZoom: 19,
      }
    ).addTo(map);

    // Zoom Controls top right
    L.control.zoom({ position: 'topright' }).addTo(map);

    markersLayerRef.current = L.layerGroup().addTo(map);
    coverageLayerRef.current = L.layerGroup().addTo(map);
    corridorLayerRef.current = L.layerGroup().addTo(map);

    map.on('click', (e: L.LeafletMouseEvent) => {
      if (isProbing && onRadiusProbe) {
        onRadiusProbe(e.latlng.lat, e.latlng.lng, probeRadius);
        setIsProbing(false);
      }
    });

    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // 2. Render Markers and Coverage Circles
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || !markersLayerRef.current || !coverageLayerRef.current) return;

    markersLayerRef.current.clearLayers();
    coverageLayerRef.current.clearLayers();

    filteredCameras.forEach((cam) => {
      if (!cam.latitude || !cam.longitude) return;

      const isSelected = selectedCamera?.id === cam.id;
      const statusClass = cam.status.toLowerCase();

      // Custom Color Status Icon
      const markerHtml = `
        <div class="leaflet-cctv-marker ${statusClass} ${isSelected ? 'selected' : ''}">
          <div class="marker-pulse"></div>
          <div class="marker-core">
            <span class="marker-dot"></span>
          </div>
          <div class="marker-tooltip-badge">${cam.camera_code}</div>
        </div>
      `;

      const customIcon = L.divIcon({
        className: 'leaflet-custom-cctv-icon',
        html: markerHtml,
        iconSize: [28, 28],
        iconAnchor: [14, 14],
      });

      const marker = L.marker([cam.latitude, cam.longitude], { icon: customIcon });

      // Direct click → open live stream modal immediately
      marker.on('click', () => {
        onSelectCamera(cam);
        openLiveStreamRef.current(cam);
      });

      // Hover tooltip for quick camera code preview
      marker.bindTooltip(
        `<strong>${cam.camera_code}</strong> — ${cam.name}<br/><span style="opacity:0.7">${cam.district || 'Gujarat'} • ${cam.city || ''}</span>`,
        {
          className: 'cctv-dark-tooltip',
          direction: 'top',
          offset: [0, -14],
          opacity: 0.95,
        }
      );

      markersLayerRef.current?.addLayer(marker);

      // Estimated Coverage Radius Circle
      if (showCoverageCircles) {
        const radiusMeters = 180; // Estimated coverage radius
        const circleColor = cam.status === 'ONLINE' ? '#00f0ff' : cam.status === 'DEGRADED' ? '#f59e0b' : '#ef4444';

        const circle = L.circle([cam.latitude, cam.longitude], {
          radius: radiusMeters,
          color: circleColor,
          weight: 1,
          fillColor: circleColor,
          fillOpacity: 0.12,
          dashArray: '3, 4',
        });
        coverageLayerRef.current?.addLayer(circle);
      }
    });
  }, [filteredCameras, selectedCamera, showCoverageCircles]);

  // 3. Render Route Corridor if provided
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || !corridorLayerRef.current) return;

    corridorLayerRef.current.clearLayers();

    if (corridorPoints) {
      const latlngs: [number, number][] = [
        [corridorPoints.start_lat, corridorPoints.start_lon],
        [corridorPoints.end_lat, corridorPoints.end_lon],
      ];

      const polyline = L.polyline(latlngs, {
        color: '#00ffcc',
        weight: 4,
        dashArray: '6, 8',
        opacity: 0.85,
      });

      corridorLayerRef.current.addLayer(polyline);
      map.fitBounds(polyline.getBounds(), { padding: [40, 40] });
    }
  }, [corridorPoints]);

  const handleResetView = () => {
    mapInstanceRef.current?.setView(GUJARAT_CENTER, DEFAULT_ZOOM);
    onSelectCamera(null);
  };

  return (
    <div className="gis-map-container-leaflet">
      {/* Top Map Control Bar */}
      <div className="map-toolbar">
        <div className="filter-group">
          <label className="filter-label">
            <Filter size={12} className="text-cyan" />
            <span>DISTRICT:</span>
          </label>
          <select
            value={districtFilter}
            onChange={(e) => setDistrictFilter(e.target.value)}
            className="map-select"
          >
            <option value="ALL">ALL DISTRICTS ({districts.length})</option>
            {districts.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label className="filter-label">
            <Shield size={12} className="text-cyan" />
            <span>DEPT:</span>
          </label>
          <select
            value={departmentFilter}
            onChange={(e) => setDepartmentFilter(e.target.value)}
            className="map-select"
          >
            <option value="ALL">ALL DEPARTMENTS ({departments.length})</option>
            {departments.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label className="filter-label">
            <Activity size={12} className="text-cyan" />
            <span>STATUS:</span>
          </label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="map-select"
          >
            <option value="ALL">ALL STATUSES</option>
            <option value="ONLINE">ONLINE / LIVE</option>
            <option value="OFFLINE">OFFLINE</option>
            <option value="DEGRADED">DEGRADED</option>
            <option value="MAINTENANCE">MAINTENANCE</option>
          </select>
        </div>

        <div className="map-actions-group">
          <button
            onClick={() => setShowCoverageCircles(!showCoverageCircles)}
            className={`btn-map-tool ${showCoverageCircles ? 'active' : ''}`}
            title="Toggle Coverage Radii"
          >
            <Radio size={13} />
            <span>COVERAGE ({showCoverageCircles ? 'ON' : 'OFF'})</span>
          </button>

          <button
            onClick={handleResetView}
            className="btn-map-tool"
            title="Reset Gujarat Map View"
          >
            <LocateFixed size={13} />
            <span>RESET VIEW</span>
          </button>
        </div>

        <div className="map-stats-pill">
          <Compass size={13} className="text-cyan animate-spin" style={{ animationDuration: '10s' }} />
          <span>{filteredCameras.length} ASSETS MAPPED</span>
        </div>
      </div>

      {/* Real Leaflet Map Viewport */}
      <div className="gis-leaflet-viewport" ref={mapContainerRef}>
        {/* Coverage Legend Watermark */}
        <div className="gis-legend-overlay">
          <div className="legend-row">
            <span className="legend-dot green"></span>
            <span>ONLINE / LIVE</span>
          </div>
          <div className="legend-row">
            <span className="legend-dot red"></span>
            <span>OFFLINE</span>
          </div>
          <div className="legend-row">
            <span className="legend-dot yellow"></span>
            <span>DEGRADED</span>
          </div>
          <div className="legend-row">
            <span className="legend-circle-sample"></span>
            <span>ESTIMATED COVERAGE (180m)</span>
          </div>
        </div>

        {/* Selected Camera Inspector Flyout with Live Feed */}
        {selectedCamera && (
          <div className="gis-details-flyout has-video">
            <div className="flyout-header">
              <div className="flyout-title-col">
                <span className="flyout-code">{selectedCamera.camera_code}</span>
                <h4 className="flyout-name">{selectedCamera.name}</h4>
              </div>
              <div className="flyout-header-actions">
                <StatusBadge status={selectedCamera.status} />
                <button
                  onClick={() => onSelectCamera(null)}
                  className="btn-flyout-close"
                  title="Close"
                >✕</button>
              </div>
            </div>

            {/* Embedded Live Video Feed */}
            <div className="flyout-video-embed">
              <CameraPlayer
                camera={selectedCamera}
                status={selectedCamera.status}
                protocol="HLS"
                fps={selectedCamera.fps || 30}
                quality="EXCELLENT"
              />
              <button
                onClick={() => setLiveStreamModalCam(selectedCamera)}
                className="btn-flyout-expand"
                title="Expand Fullscreen"
              >
                <Maximize2 size={14} />
              </button>
            </div>

            <div className="flyout-body">
              <div className="flyout-meta-row">
                <span className="lbl">POSTGIS COORDS:</span>
                <span className="val font-mono">{selectedCamera.latitude.toFixed(5)}, {selectedCamera.longitude.toFixed(5)}</span>
              </div>
              <div className="flyout-meta-row">
                <span className="lbl">DISTRICT:</span>
                <span className="val">{selectedCamera.district || 'Gujarat Central'}</span>
              </div>
              <div className="flyout-meta-row">
                <span className="lbl">CITY:</span>
                <span className="val">{selectedCamera.city || selectedCamera.district || 'Gujarat'}</span>
              </div>
              <div className="flyout-meta-row">
                <span className="lbl">DEPARTMENT:</span>
                <span className="val">{selectedCamera.department_name || 'Gujarat Police / Smart City'}</span>
              </div>
              <div className="flyout-meta-row">
                <span className="lbl">TYPE:</span>
                <span className="val">{selectedCamera.camera_type}</span>
              </div>
              <div className="flyout-meta-row">
                <span className="lbl">AI:</span>
                <span className="val text-cyan">{selectedCamera.ai_enabled ? 'ANPR · TRACKING · CROWD' : 'STANDARD'}</span>
              </div>

              {/* Quick Action Buttons */}
              <div className="flyout-actions-row">
                <button
                  onClick={() => setLiveStreamModalCam(selectedCamera)}
                  className="btn-flyout-primary"
                >
                  <Maximize2 size={13} />
                  <span>FULLSCREEN</span>
                </button>
                <button
                  onClick={() => onRadiusProbe && onRadiusProbe(selectedCamera.latitude, selectedCamera.longitude, 3000)}
                  className="btn-flyout-secondary"
                >
                  <Radio size={13} />
                  <span>NEARBY (3KM)</span>
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Live Stream Modal — Opens directly on marker click */}
      {liveStreamModalCam && (
        <div className="modal-overlay" onClick={() => setLiveStreamModalCam(null)}>
          <div className="modal-content modal-video-dialog" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title-wrap">
                <h3 className="modal-title">{liveStreamModalCam.camera_code} // {liveStreamModalCam.name}</h3>
                <span className="modal-subtitle">
                  {liveStreamModalCam.district} • {liveStreamModalCam.city || liveStreamModalCam.district} • {liveStreamModalCam.camera_type} • [{liveStreamModalCam.latitude.toFixed(4)}, {liveStreamModalCam.longitude.toFixed(4)}]
                </span>
              </div>
              <button onClick={() => setLiveStreamModalCam(null)} className="btn-modal-close">✕</button>
            </div>
            <div className="modal-video-body">
              <CameraPlayer
                camera={liveStreamModalCam}
                status={liveStreamModalCam.status}
                protocol="HLS"
                fps={liveStreamModalCam.fps || 30}
                quality="EXCELLENT"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
