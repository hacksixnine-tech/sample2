import { apiClient } from './client';
import { District, ApiResponse } from '../types';

export const districtsApi = {
  list: (params: { zone?: string; search?: string } = {}) => {
    const query = new URLSearchParams();
    if (params.zone) query.append('zone', params.zone);
    if (params.search) query.append('search', params.search);
    const qs = query.toString() ? `?${query.toString()}` : '';
    return apiClient<ApiResponse<District[]>>(`/districts${qs}`);
  },
};
