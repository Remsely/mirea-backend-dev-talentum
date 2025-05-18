import { atom } from 'jotai';
import type { User, Employee, AuthResponse } from '../types/auth';

// Auth state atoms
export const accessTokenAtom = atom<string | null>(
  localStorage.getItem('accessToken')
);

export const refreshTokenAtom = atom<string | null>(
  localStorage.getItem('refreshToken')
);

export const isAuthenticatedAtom = atom<boolean>(
  (get) => !!get(accessTokenAtom)
);

export const currentUserAtom = atom<User | null>(null);
export const employeeProfileAtom = atom<Employee | null>(null);
export const employeeIdAtom = atom<number | null>(
  (get) => get(employeeProfileAtom)?.id || null
);
export const authAtom = atom<AuthResponse | null>(null);

// User role atoms
export const isEmployeeAtom = atom<boolean>(
  (get) => get(currentUserAtom)?.role === 'employee'
);

export const isManagerAtom = atom<boolean>(
  (get) => !!get(employeeProfileAtom)?.is_manager
);

export const isExpertiseLeaderAtom = atom<boolean>(
  (get) => get(currentUserAtom)?.role === 'expertise_leader'
);

export const isAdminAtom = atom<boolean>(
  (get) => get(currentUserAtom)?.role === 'admin'
);

// Action atoms
export const setAuthTokensAtom = atom(
  null,
  (_get, set, authResponse: AuthResponse) => {
    localStorage.setItem('accessToken', authResponse.access);
    localStorage.setItem('refreshToken', authResponse.refresh);
    
    set(accessTokenAtom, authResponse.access);
    set(refreshTokenAtom, authResponse.refresh);
    set(authAtom, authResponse);
    
    // Set user and employee data
    const user: User = {
      id: authResponse.user_id,
      username: authResponse.username,
      email: authResponse.email,
      first_name: authResponse.full_name.split(' ')[0] || '',
      last_name: authResponse.full_name.split(' ')[1] || '',
      role: authResponse.role
    };
    set(currentUserAtom, user);
    
    if (authResponse.has_employee_profile && authResponse.employee_id) {
      const employee: Partial<Employee> = {
        id: authResponse.employee_id,
        position: authResponse.position || '',
        is_manager: authResponse.is_manager,
        profile_photo_url: authResponse.profile_photo_url
      };
      set(employeeProfileAtom, employee as Employee);
    }
  }
);

export const clearAuthAtom = atom(
  null,
  (_get, set) => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    
    set(accessTokenAtom, null);
    set(refreshTokenAtom, null);
    set(currentUserAtom, null);
    set(employeeProfileAtom, null);
    set(authAtom, null);
  }
); 