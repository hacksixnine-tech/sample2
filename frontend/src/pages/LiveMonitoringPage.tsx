import React, { useState, useEffect } from 'react';
import { Camera } from '../types';
import { camerasApi } from '../api/cameras';
import { CameraCard } from '../components/camera/CameraCard';
import { LoadingState } from '../components/common/LoadingError';
import { LayoutGrid, Grid3X3, Grid, Square, Filter, RefreshCw, Layers } from 'lucide-react';

export const LiveMonitoringPage: React.FC = () => {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [layout, setLayout] = useState<'1' | '4' | '9' | '16' | '30'>('4');
  const [filterDistrict, setFilterDistrict] = useState<string>('ALL');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [selectedCamera, setSelectedCamera] = useState<Camera | null>(null);

  const fetchCameras = async () => {
    setIsLoading(true);
    try {
      let loaded: Camera[] = [];
      try {
        const res = await camerasApi.list({ page_size: 30 });
        if (res && res.data && res.data.length > 0) {
          loaded = res.data;
        }
      } catch {
        // Fallback
      }

      if (loaded.length === 0) {
        loaded = await camerasApi.fetchDirectCorp8Catalog();
      }

      setCameras(loaded);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCameras();
  }, []);

  const districts = Array.from(new Set(cameras.map((c) => c.district).filter(Boolean)));

  const filteredCameras = cameras.filter((c) => {
    if (filterDistrict !== 'ALL' && c.district !== filterDistrict) return false;
    return true;
  });

  const countToDisplay = layout === '1' ? 1 : layout === '4' ? 4 : layout === '9' ? 9 : layout === '16' ? 16 : 30;
  const displayCameras = filteredCameras.slice(0, countToDisplay);

  return (
    <div className="live-monitoring-page">
      {/* Top Controls Toolbar */}
      <div className="monitoring-toolbar">
        <div className="toolbar-left">
          <h2 className="page-title">LIVE MULTI-CAMERA MONITORING WALL</h2>
          <span className="live-pill">● {filteredCameras.length} STREAMS INGESTED</span>
        </div>

        <div className="toolbar-right">
          {/* District Filter */}
          <div className="district-filter-select">
            <Filter size={12} className="text-cyan" />
            <select
              value={filterDistrict}
              onChange={(e) => setFilterDistrict(e.target.value)}
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

          {/* Layout Switcher */}
          <div className="layout-btn-group">
            <button
              onClick={() => setLayout('1')}
              className={`btn-layout ${layout === '1' ? 'active' : ''}`}
              title="1-Way Focused Mode"
            >
              <Square size={13} />
              <span>1x1</span>
            </button>
            <button
              onClick={() => setLayout('4')}
              className={`btn-layout ${layout === '4' ? 'active' : ''}`}
              title="4-Way Quad (2x2)"
            >
              <LayoutGrid size={13} />
              <span>2x2</span>
            </button>
            <button
              onClick={() => setLayout('9')}
              className={`btn-layout ${layout === '9' ? 'active' : ''}`}
              title="9-Way Matrix (3x3)"
            >
              <Grid3X3 size={13} />
              <span>3x3</span>
            </button>
            <button
              onClick={() => setLayout('16')}
              className={`btn-layout ${layout === '16' ? 'active' : ''}`}
              title="16-Way High Density (4x4)"
            >
              <Grid size={13} />
              <span>4x4</span>
            </button>
            <button
              onClick={() => setLayout('30')}
              className={`btn-layout ${layout === '30' ? 'active' : ''}`}
              title="All 30 Live Feeds"
            >
              <Layers size={13} />
              <span>ALL 30</span>
            </button>
          </div>

          <button onClick={fetchCameras} className="btn-icon-action" title="Refresh Streams">
            <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {/* Dynamic Responsive Video Grid */}
      {isLoading ? (
        <LoadingState message="Establishing HLS stream sessions across surveillance grid..." />
      ) : (
        <div className={`monitoring-grid grid-layout-${layout}`}>
          {displayCameras.map((cam) => (
            <CameraCard
              key={cam.id}
              camera={cam}
              isFocused={selectedCamera?.id === cam.id}
              onSelect={setSelectedCamera}
            />
          ))}
        </div>
      )}
    </div>
  );
};
