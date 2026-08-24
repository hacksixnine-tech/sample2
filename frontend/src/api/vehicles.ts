import { apiClient, API_BASE_URL } from './client';
import {
  ApiResponse,
  VehicleMovementHistory,
  VehicleRoute,
  VehicleSummary,
} from '../types';

export interface VehicleTimelineFilterParams {
  timestamp_from?: string;
  timestamp_to?: string;
  district?: string;
  camera_id?: string;
  watchlist_only?: boolean;
  order?: 'asc' | 'desc';
  limit?: number;
}

export const vehiclesApi = {
  /**
   * Fetch consolidated vehicle summary metrics
   */
  getVehicleSummary: (identifier: string) => {
    return apiClient<ApiResponse<VehicleSummary>>(`/vehicles/${encodeURIComponent(identifier)}/summary`);
  },

  /**
   * Fetch chronological vehicle sightings timeline with transition telemetry
   */
  getVehicleTimeline: (identifier: string, params: VehicleTimelineFilterParams = {}) => {
    const query = new URLSearchParams();
    if (params.timestamp_from) query.append('timestamp_from', params.timestamp_from);
    if (params.timestamp_to) query.append('timestamp_to', params.timestamp_to);
    if (params.district) query.append('district', params.district);
    if (params.camera_id) query.append('camera_id', params.camera_id);
    if (params.watchlist_only) query.append('watchlist_only', 'true');
    if (params.order) query.append('order', params.order);
    if (params.limit) query.append('limit', String(params.limit));

    const qs = query.toString() ? `?${query.toString()}` : '';
    return apiClient<ApiResponse<VehicleMovementHistory>>(`/vehicles/${encodeURIComponent(identifier)}/timeline${qs}`);
  },

  /**
   * Fetch GIS-ready observed camera sequence route
   */
  getVehicleRoute: (identifier: string, params: { timestamp_from?: string; timestamp_to?: string } = {}) => {
    const query = new URLSearchParams();
    if (params.timestamp_from) query.append('timestamp_from', params.timestamp_from);
    if (params.timestamp_to) query.append('timestamp_to', params.timestamp_to);

    const qs = query.toString() ? `?${query.toString()}` : '';
    return apiClient<ApiResponse<VehicleRoute>>(`/vehicles/${encodeURIComponent(identifier)}/route${qs}`);
  },

  /**
   * Export vehicle movement history as CSV
   */
  exportVehicleCsv: async (identifier: string, params: VehicleTimelineFilterParams = {}): Promise<Blob> => {
    const query = new URLSearchParams();
    if (params.timestamp_from) query.append('timestamp_from', params.timestamp_from);
    if (params.timestamp_to) query.append('timestamp_to', params.timestamp_to);
    if (params.district) query.append('district', params.district);
    if (params.camera_id) query.append('camera_id', params.camera_id);
    if (params.watchlist_only) query.append('watchlist_only', 'true');

    const qs = query.toString() ? `?${query.toString()}` : '';
    const token = localStorage.getItem('phantom_auth_token');
    const headers: Record<string, string> = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const res = await fetch(`${API_BASE_URL}/vehicles/${encodeURIComponent(identifier)}/export${qs}`, {
      headers,
    });
    return await res.blob();
  },
};
