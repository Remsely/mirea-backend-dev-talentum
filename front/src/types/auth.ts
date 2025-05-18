export type UserRole = 'employee' | 'expertise_leader' | 'admin';

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  is_active?: boolean;
  date_joined?: string;
  registration_dttm?: string;
}

export interface Employee {
  id: number;
  user: User;
  hire_dt: string;
  position: string;
  manager: number | null;
  manager_name: string | null;
  profile_photo_url: string | null;
  is_manager?: boolean;
  subordinates?: Employee[];
}

export interface AuthResponse {
  access: string;
  refresh: string;
  user_id: number;
  username: string;
  email: string;
  role: UserRole;
  full_name: string;
  employee_id?: number;
  position?: string;
  has_employee_profile: boolean;
  is_manager: boolean;
  profile_photo_url?: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RefreshTokenRequest {
  refresh: string;
} 