import { apiClient } from './client';
import { Incident, WatchlistEntry, AuditLog, ApiResponse, PaginatedResponse } from '../types';

export const incidentsApi = {
  list: (status?: string) => {
    const qs = status ? `?status=${status}` : '';
    return apiClient<PaginatedResponse<Incident>>(`/incidents${qs}`);
  },
  getById: (id: string) => apiClient<ApiResponse<Incident>>(`/incidents/${id}`),
};

export const watchlistsApi = {
  list: (type?: string) => {
    const qs = type ? `?type=${type}` : '';
    return apiClient<PaginatedResponse<WatchlistEntry>>(`/watchlists${qs}`);
  },
};

export const auditApi = {
  list: (limit: number = 50) => apiClient<PaginatedResponse<AuditLog>>(`/audit?limit=${limit}`),
};
