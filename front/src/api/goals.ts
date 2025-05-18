import axiosInstance from './axios';
import type { Goal, GoalCreate, GoalUpdate, Progress } from '../types/goals';

export const goalsApi = {
  // Get all goals (filtered by user's role and permissions)
  getAll: async (): Promise<Goal[]> => {
    const response = await axiosInstance.get<Goal[]>('/goals/');
    return response.data;
  },

  // Get goals for the current user
  getMyGoals: async (): Promise<Goal[]> => {
    const response = await axiosInstance.get<Goal[]>('/goals/');
    return response.data;
  },

  // Get goals for a specific employee (for managers)
  getEmployeeGoals: async (employeeId: number): Promise<Goal[]> => {
    const response = await axiosInstance.get<Goal[]>(`/goals/employee/${employeeId}/`);
    return response.data;
  },

  // Get a single goal by ID
  getById: async (id: number): Promise<Goal> => {
    const response = await axiosInstance.get<Goal>(`/goals/${id}/`);
    return response.data;
  },

  // Create a new goal
  create: async (goal: GoalCreate): Promise<Goal> => {
    const response = await axiosInstance.post<Goal>('/goals/', goal);
    return response.data;
  },

  // Update an existing goal
  update: async (id: number, goal: GoalUpdate): Promise<Goal> => {
    const response = await axiosInstance.patch<Goal>(`/goals/${id}/`, goal);
    return response.data;
  },

  // Delete a goal
  delete: async (id: number): Promise<void> => {
    await axiosInstance.delete(`/goals/${id}/`);
  },

  // Submit a goal for approval
  submit: async (id: number): Promise<Goal> => {
    const response = await axiosInstance.post<Goal>(`/goals/${id}/submit/`);
    return response.data;
  },

  // Approve a goal (manager only)
  approve: async (id: number): Promise<Goal> => {
    const response = await axiosInstance.post<Goal>(`/goals/${id}/approve/`);
    return response.data;
  },

  // Complete a goal
  complete: async (id: number): Promise<Goal> => {
    const response = await axiosInstance.post<Goal>(`/goals/${id}/complete/`);
    return response.data;
  },

  // Get progress entries for a goal
  getProgress: async (goalId: number): Promise<Progress[]> => {
    const response = await axiosInstance.get<Progress[]>(`/goals/${goalId}/progress/`);
    return response.data;
  },

  // Add a progress entry
  addProgress: async (goalId: number, progress: Omit<Progress, 'id' | 'goal'>): Promise<Progress> => {
    const response = await axiosInstance.post<Progress>(`/goals/${goalId}/progress/`, progress);
    return response.data;
  },

  // Get goals pending approval (for managers)
  getPendingApprovalGoals: async (): Promise<Goal[]> => {
    const response = await axiosInstance.get<Goal[]>('/goals/pending_approval/');
    return response.data;
  }
}; 