import React from 'react';
import { CameraStatus } from '../../types';

export const CameraStatusBadge: React.FC<{ status: CameraStatus }> = ({ status }) => {
  const isOnline = status === 'ONLINE';
  const isDegraded = status === 'DEGRADED';
  const isMaint = status === 'MAINTENANCE';

  let statusClass = 'status-offline';
  if (isOnline) statusClass = 'status-online';
  else if (isDegraded) statusClass = 'status-degraded';
  else if (isMaint) statusClass = 'status-maintenance';

  return (
    <div className={`cam-status-pill ${statusClass}`}>
      <span className="cam-status-dot" />
      <span>{status}</span>
    </div>
  );
};
