import { apiClient } from './client';
import { ANPRRecord, ApiResponse, PaginatedResponse } from '../types';

export interface ANPRQueryParams {
  plate?: string;
  camera_id?: string;
  district?: string;
  watchlist_only?: boolean;
  limit?: number;
}

export const anprApi = {
  list: (params: ANPRQueryParams = {}) => {
    const query = new URLSearchParams();
    if (params.plate) query.append('plate', params.plate);
    if (params.camera_id) query.append('camera_id', params.camera_id);
    if (params.district) query.append('district', params.district);
    if (params.watchlist_only) query.append('watchlist_only', 'true');
    if (params.limit) query.append('limit', String(params.limit));

    const qs = query.toString() ? `?${query.toString()}` : '';
    return apiClient<PaginatedResponse<ANPRRecord>>(`/anpr${qs}`);
  },

  searchPlate: (plateNumber: string) =>
    apiClient<ApiResponse<ANPRRecord[]>>(`/vehicles/search?plate=${encodeURIComponent(plateNumber)}`),
};
