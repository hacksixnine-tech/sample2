import { apiClient } from './client';
import { Department, ApiResponse, PaginatedResponse } from '../types';

export const departmentsApi = {
  list: (params: { is_active?: boolean; search?: string; page_size?: number } = {}) => {
    const query = new URLSearchParams();
    if (params.is_active !== undefined) query.append('is_active', String(params.is_active));
    if (params.search) query.append('search', params.search);
    if (params.page_size) query.append('page_size', String(params.page_size));
    const qs = query.toString() ? `?${query.toString()}` : '';
    return apiClient<PaginatedResponse<Department>>(`/departments${qs}`);
  },

  getById: (id: string) => apiClient<ApiResponse<Department>>(`/departments/${id}`),
};
