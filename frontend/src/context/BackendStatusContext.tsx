import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { healthApi } from '../api/health';
import { HealthResponse, ReadinessResponse, SystemInfo } from '../types';

interface BackendStatusContextType {
  isConnected: boolean;
  isDbReady: boolean;
  health: HealthResponse | null;
  readiness: ReadinessResponse | null;
  systemInfo: SystemInfo | null;
  latencyMs: number | null;
  lastChecked: Date | null;
  error: string | null;
  refreshStatus: () => Promise<void>;
}

const BackendStatusContext = createContext<BackendStatusContextType | undefined>(undefined);

export const BackendStatusProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [isDbReady, setIsDbReady] = useState<boolean>(false);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null);
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [latencyMs, setLatencyMs] = useState<number | null>(null);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refreshStatus = useCallback(async () => {
    const startTime = performance.now();
    try {
      const [healthRes, readyRes, infoRes] = await Promise.allSettled([
        healthApi.checkHealth(),
        healthApi.getReadiness(),
        healthApi.getSystemInfo(),
      ]);

      const roundTrip = Math.round(performance.now() - startTime);
      setLatencyMs(roundTrip);
      setLastChecked(new Date());

      if (healthRes.status === 'fulfilled') {
        setHealth(healthRes.value);
        setIsConnected(true);
        setError(null);
      } else {
        setIsConnected(false);
        setError(healthRes.reason?.message || 'Backend connection failed');
      }

      if (readyRes.status === 'fulfilled') {
        setReadiness(readyRes.value);
        setIsDbReady(readyRes.value.status === 'ready' && readyRes.value.database?.connected);
      } else {
        setIsDbReady(false);
      }

      if (infoRes.status === 'fulfilled') {
        setSystemInfo(infoRes.value);
      }
    } catch (err: unknown) {
      setIsConnected(false);
      setIsDbReady(false);
      const msg = err instanceof Error ? err.message : 'Unknown error';
      setError(msg);
    }
  }, []);

  useEffect(() => {
    refreshStatus();
    const interval = setInterval(refreshStatus, 15000); // Poll every 15s
    return () => clearInterval(interval);
  }, [refreshStatus]);

  return (
    <BackendStatusContext.Provider
      value={{
        isConnected,
        isDbReady,
        health,
        readiness,
        systemInfo,
        latencyMs,
        lastChecked,
        error,
        refreshStatus,
      }}
    >
      {children}
    </BackendStatusContext.Provider>
  );
};

export const useBackendStatus = () => {
  const context = useContext(BackendStatusContext);
  if (!context) {
    throw new Error('useBackendStatus must be used within BackendStatusProvider');
  }
  return context;
};
