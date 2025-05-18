import axiosInstance from './axios';
import type { Goal, GoalCreate, GoalUpdate, Progress } from '../types/goals';

// Вспомогательная функция для нормализации полей цели
const normalizeGoal = (goal: Goal): Goal => {
  // Обеспечиваем совместимость полей progress_entries и progress_updates
  if (goal.progress_updates && !goal.progress_entries) {
    goal.progress_entries = goal.progress_updates;
  }
  else if (goal.progress_entries && !goal.progress_updates) {
    goal.progress_updates = goal.progress_entries;
  }
  return goal;
};

// Нормализация массива целей
const normalizeGoals = (goals: Goal[]): Goal[] => {
  return goals.map(normalizeGoal);
};

export const goalsApi = {
  // Get all goals (filtered by user's role and permissions)
  getAll: async (): Promise<Goal[]> => {
    try {
      const response = await axiosInstance.get<Goal[]>('/goals/');
      return normalizeGoals(response.data);
    } catch (error) {
      console.error('Error fetching all goals:', error);
      return [];
    }
  },

  // Get goals for the current user
  getMyGoals: async (): Promise<Goal[]> => {
    try {
      // First try the specific endpoint for my goals
      const response = await axiosInstance.get<Goal[]>('/goals/my_goals/');
      return normalizeGoals(response.data);
    } catch (error) {
      console.error('Error fetching my goals with specific endpoint:', error);
      // Fall back to the main endpoint which should filter by current user
      try {
        const fallbackResponse = await axiosInstance.get<Goal[]>('/goals/');
        return normalizeGoals(fallbackResponse.data);
      } catch (fallbackError) {
        console.error('Error fetching my goals with fallback:', fallbackError);
        return [];
      }
    }
  },

  // Get goals for a specific employee (for managers)
  getEmployeeGoals: async (employeeId: number): Promise<Goal[]> => {
    try {
      const response = await axiosInstance.get<Goal[]>(`/goals/employee/${employeeId}/`);
      return normalizeGoals(response.data);
    } catch (error) {
      console.error(`Error fetching goals for employee ${employeeId}:`, error);
      return [];
    }
  },

  // Get a single goal by ID
  getById: async (id: number): Promise<Goal> => {
    try {
      const response = await axiosInstance.get<Goal>(`/goals/${id}/`);
      return normalizeGoal(response.data);
    } catch (error) {
      console.error(`Error fetching goal ${id}:`, error);
      throw error;
    }
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
    try {
      const response = await axiosInstance.get<Goal[]>('/goals/pending_approval/');
      return response.data;
    } catch (error) {
      console.error('Error fetching pending approval goals:', error);
      return [];
    }
  }
}; 