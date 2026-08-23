import React from 'react';
import { ANPRRecord } from '../../types';
import { Car, AlertTriangle, ShieldCheck, MapPin, Clock } from 'lucide-react';

export const ANPRDetectionCard: React.FC<{ record: ANPRRecord }> = ({ record }) => {
  return (
    <div className={`anpr-record-card ${record.matched_watchlist ? 'watchlist-hit' : ''}`}>
      <div className="anpr-plate-row">
        <div className="plate-badge-visual">
          <span className="plate-country-tag">IND</span>
          <span className="plate-number-text">{record.plate_number}</span>
        </div>

        {record.matched_watchlist ? (
          <div className="watchlist-alert-badge">
            <AlertTriangle size={12} />
            <span>{record.watchlist_type || 'WATCHLIST HIT'}</span>
          </div>
        ) : (
          <div className="nominal-badge">
            <ShieldCheck size={12} />
            <span>CLEARED</span>
          </div>
        )}
      </div>

      <div className="anpr-meta-grid">
        <div className="meta-cell">
          <span className="meta-lbl">VEHICLE TYPE</span>
          <span className="meta-val">
            <Car size={12} className="text-cyan" />
            {record.vehicle_type || 'MOTOR VEHICLE'} ({record.vehicle_color || 'UNKNOWN'})
          </span>
        </div>

        <div className="meta-cell">
          <span className="meta-lbl">CAMERA NODE</span>
          <span className="meta-val">{record.camera_name}</span>
        </div>

        <div className="meta-cell">
          <span className="meta-lbl">CONFIDENCE</span>
          <span className="meta-val text-healthy">{Math.round(record.confidence * 100)}%</span>
        </div>

        <div className="meta-cell">
          <span className="meta-lbl">TIMESTAMP</span>
          <span className="meta-val">
            <Clock size={11} className="text-muted" />
            {new Date(record.timestamp).toLocaleTimeString()}
          </span>
        </div>
      </div>

      {record.district && (
        <div className="anpr-footer-loc">
          <MapPin size={11} className="text-cyan" />
          <span>{record.district}</span>
        </div>
      )}
    </div>
  );
};
