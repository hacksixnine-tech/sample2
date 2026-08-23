import React from 'react';
import { AlertSeverity, AlertStatus, CameraStatus } from '../../types';

interface StatusBadgeProps {
  status: AlertSeverity | AlertStatus | CameraStatus | string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'sm' }) => {
  const normalized = status.toUpperCase();

  let colorClass = 'badge-neutral';

  switch (normalized) {
    case 'CRITICAL':
    case 'SEV-1':
    case 'OFFLINE':
      colorClass = 'badge-critical';
      break;
    case 'HIGH':
    case 'SEV-2':
    case 'DEGRADED':
    case 'WARNING':
      colorClass = 'badge-warning';
      break;
    case 'MEDIUM':
    case 'ATTENTION':
    case 'MAINTENANCE':
      colorClass = 'badge-attention';
      break;
    case 'ONLINE':
    case 'RESOLVED':
    case 'HEALTHY':
    case 'READY':
      colorClass = 'badge-healthy';
      break;
    case 'LOW':
    case 'INFO':
    case 'NEW':
    case 'ACKNOWLEDGED':
      colorClass = 'badge-info';
      break;
    default:
      colorClass = 'badge-neutral';
  }

  return (
    <span className={`status-badge-pill ${colorClass} size-${size}`}>
      <span className="badge-dot" />
      {normalized}
    </span>
  );
};
