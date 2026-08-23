import React from 'react';
import { AlertTriangle, ServerOff, Loader2, Inbox } from 'lucide-react';

interface LoadingStateProps {
  message?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({ message = 'Fetching surveillance telemetry...' }) => (
  <div className="state-container loading-state" role="status">
    <Loader2 size={24} className="animate-spin text-cyan" />
    <span className="state-text">{message}</span>
  </div>
);

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Service Error',
  message,
  onRetry,
}) => (
  <div className="state-container error-state" role="alert">
    <AlertTriangle size={24} className="text-danger" />
    <div className="state-info">
      <h4 className="state-title">{title}</h4>
      <p className="state-desc">{message}</p>
    </div>
    {onRetry && (
      <button onClick={onRetry} className="btn-retry">
        Retry Connection
      </button>
    )}
  </div>
);

interface BackendUnavailableProps {
  endpointName?: string;
  onRetry?: () => void;
}

export const BackendUnavailableState: React.FC<BackendUnavailableProps> = ({
  endpointName = 'Backend Service',
  onRetry,
}) => (
  <div className="state-container backend-unavailable-state" role="alert">
    <ServerOff size={28} className="text-warning" />
    <div className="state-info">
      <h4 className="state-title">DATA UNAVAILABLE — {endpointName.toUpperCase()} OFFLINE</h4>
      <p className="state-desc">
        Unable to reach the FastAPI endpoint. Verify that the backend server is running on port 8000.
      </p>
    </div>
    {onRetry && (
      <button onClick={onRetry} className="btn-retry">
        Re-probe Service
      </button>
    )}
  </div>
);

interface EmptyStateProps {
  title?: string;
  message?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'No Records Found',
  message = 'There are no active entries matching the specified criteria.',
}) => (
  <div className="state-container empty-state">
    <Inbox size={28} className="text-muted" />
    <div className="state-info">
      <h4 className="state-title">{title}</h4>
      <p className="state-desc">{message}</p>
    </div>
  </div>
);
