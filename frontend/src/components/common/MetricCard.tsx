import React from 'react';

interface MetricCardProps {
  title: string;
  value: string | number | null | undefined;
  subValue?: string;
  icon: React.ElementType;
  trend?: 'positive' | 'negative' | 'neutral' | 'warning';
  trendLabel?: string;
  isLoading?: boolean;
  unavailableText?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subValue,
  icon: Icon,
  trend = 'neutral',
  trendLabel,
  isLoading = false,
  unavailableText = 'DATA UNAVAILABLE',
}) => {
  const isDataUnavailable = value === null || value === undefined;

  return (
    <div className="metric-card-box" tabIndex={0}>
      <div className="metric-header">
        <span className="metric-title">{title}</span>
        <div className={`metric-icon-wrap icon-${trend}`}>
          <Icon size={16} />
        </div>
      </div>

      <div className="metric-body">
        {isLoading ? (
          <div className="metric-loading-skeleton"></div>
        ) : isDataUnavailable ? (
          <div className="metric-unavailable">{unavailableText}</div>
        ) : (
          <div className="metric-value-row">
            <span className="metric-main-val">{value}</span>
            {subValue && <span className="metric-sub-val">{subValue}</span>}
          </div>
        )}
      </div>

      {trendLabel && !isDataUnavailable && !isLoading && (
        <div className={`metric-trend trend-${trend}`}>
          <span>{trendLabel}</span>
        </div>
      )}
    </div>
  );
};
