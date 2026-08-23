import { apiClient } from './client';
import { Alert, AlertStatus, ApiResponse, PaginatedResponse } from '../types';

export interface AlertFilterParams {
  severity?: string;
  status?: string;
  district?: string;
  limit?: number;
}

export const alertsApi = {
  list: (params: AlertFilterParams = {}) => {
    const query = new URLSearchParams();
    if (params.severity) query.append('severity', params.severity);
    if (params.status) query.append('status', params.status);
    if (params.district) query.append('district', params.district);
    if (params.limit) query.append('limit', String(params.limit));

    const qs = query.toString() ? `?${query.toString()}` : '';
    return apiClient<PaginatedResponse<Alert>>(`/alerts${qs}`);
  },

  getById: (id: string) => apiClient<ApiResponse<Alert>>(`/alerts/${id}`),

  updateStatus: (id: string, status: AlertStatus, notes?: string) =>
    apiClient<ApiResponse<Alert>>(`/alerts/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status, notes }),
    }),
};
