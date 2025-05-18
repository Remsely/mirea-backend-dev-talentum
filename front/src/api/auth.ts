import type { AuthResponse, LoginCredentials, RefreshTokenRequest, User, Employee } from '../types/auth';
import axiosInstance from './axios';

export const authApi = {
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    const response = await axiosInstance.post<AuthResponse>('/auth/token/', credentials);
    return response.data;
  },

  refreshToken: async (refreshToken: RefreshTokenRequest): Promise<AuthResponse> => {
    const response = await axiosInstance.post<AuthResponse>('/auth/token/refresh/', refreshToken);
    return response.data;
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await axiosInstance.get<User>('/users/me/');
    return response.data;
  },

  getEmployeeProfile: async (): Promise<Employee> => {
    const response = await axiosInstance.get<Employee>('/employees/my_profile/');
    return response.data;
  },

  getMyTeam: async (): Promise<Employee[]> => {
    const response = await axiosInstance.get<Employee[]>('/employees/my_team/');
    return response.data;
  }
}; 