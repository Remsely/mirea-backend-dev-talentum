import type { Employee } from './auth';

export type GoalStatus = 'draft' | 'pending_approval' | 'approved' | 'in_progress' | 'pending_assessment' | 'completed' | 'cancelled';

export interface Goal {
  id: number;
  title: string;
  description: string;
  expected_results: string;
  start_period: string;
  end_period: string;
  status: GoalStatus;
  employee: Employee;
  created_dttm: string;
  updated_dttm: string;
  progress_entries?: Progress[];
  progress_updates?: Progress[];
}

export type GoalCreate = Omit<Goal, 'id' | 'status' | 'created_dttm' | 'updated_dttm' | 'progress_entries' | 'progress_updates'>;

export type GoalUpdate = Partial<Omit<Goal, 'id' | 'status' | 'created_dttm' | 'updated_dttm' | 'progress_entries' | 'progress_updates'>>;

export interface Progress {
  id: number;
  goal: number;
  description: string;
  created_dttm: string;
} 