import React, { useState, useEffect } from 'react';
import { ANPRRecord } from '../types';
import { anprApi } from '../api/anpr';
import { ANPRDetectionCard } from '../components/anpr/ANPRDetectionCard';
import { LoadingState, BackendUnavailableState, EmptyState } from '../components/common/LoadingError';
import { useBackendStatus } from '../context/BackendStatusContext';
import { Car, Search, Filter, RefreshCw, ShieldAlert } from 'lucide-react';

export const ANPRVehiclesPage: React.FC = () => {
  const { isConnected } = useBackendStatus();
  const [records, setRecords] = useState<ANPRRecord[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [searchPlate, setSearchPlate] = useState<string>('');
  const [watchlistOnly, setWatchlistOnly] = useState<boolean>(false);

  const fetchANPR = async () => {
    setIsLoading(true);
    try {
      const res = await anprApi.list({
        plate: searchPlate || undefined,
        watchlist_only: watchlistOnly,
        limit: 30,
      });
      if (res && res.data) {
        setRecords(res.data);
      }
    } catch {
      setRecords([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchANPR();
  }, [watchlistOnly]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchANPR();
  };

  return (
    <div className="anpr-page-container">
      <div className="registry-header-row">
        <div>
          <h2 className="page-title">ANPR & VEHICLE SURVEILLANCE INTELLIGENCE</h2>
          <p className="page-subtitle">Real-time Gujarat RTO plate OCR recognition and automated watchlist correlation.</p>
        </div>

        <div className="stats-indicator-group">
          <div className="stat-pill">
            <Car size={13} className="text-cyan" />
            <span>1,420 OCR SCANS/HR</span>
          </div>
          <div className="stat-pill warning">
            <ShieldAlert size={13} className="text-warning" />
            <span>12 WATCHLIST HITS</span>
          </div>
        </div>
      </div>

      {/* Plate Search & Filter Bar */}
      <form onSubmit={handleSearchSubmit} className="registry-filter-bar">
        <div className="search-input-wrap">
          <Search size={14} className="text-muted" />
          <input
            type="text"
            placeholder="Search Gujarat License Plate (e.g. GJ01AB1234)..."
            value={searchPlate}
            onChange={(e) => setSearchPlate(e.target.value)}
          />
        </div>

        <div className="filter-select-group">
          <label className="checkbox-toggle">
            <input
              type="checkbox"
              checked={watchlistOnly}
              onChange={(e) => setWatchlistOnly(e.target.checked)}
            />
            <span>WATCHLIST HITS ONLY</span>
          </label>

          <button type="submit" className="btn-primary-action">
            SEARCH PLATE
          </button>

          <button type="button" onClick={fetchANPR} className="btn-icon-action" title="Refresh Feed">
            <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} />
          </button>
        </div>
      </form>

      {/* ANPR Records Grid */}
      <div className="anpr-grid-container">
        {isLoading ? (
          <LoadingState message="Connecting to AI Inference ANPR Stream..." />
        ) : !isConnected && records.length === 0 ? (
          <BackendUnavailableState endpointName="ANPR Analytics Service" onRetry={fetchANPR} />
        ) : records.length === 0 ? (
          <EmptyState title="No Plate Detections" message="No vehicle sightings matching the specified criteria." />
        ) : (
          <div className="anpr-cards-grid">
            {records.map((rec) => (
              <ANPRDetectionCard key={rec.id} record={rec} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
