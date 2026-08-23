import { apiClient } from './client';
import { HealthResponse, ReadinessResponse, SystemInfo } from '../types';

export const healthApi = {
  getLiveness: () => apiClient<HealthResponse>('/health/live'),
  getReadiness: () => apiClient<ReadinessResponse>('/health/ready'),
  getSystemInfo: () => apiClient<SystemInfo>('/info'),
  checkHealth: () => apiClient<HealthResponse>('/health'),
};
