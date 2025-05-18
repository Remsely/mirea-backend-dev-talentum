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
  (get, set, authResponse: AuthResponse) => {
    localStorage.setItem('accessToken', authResponse.access);
    localStorage.setItem('refreshToken', authResponse.refresh);
    
    set(accessTokenAtom, authResponse.access);
    set(refreshTokenAtom, authResponse.refresh);
  }
);

export const clearAuthAtom = atom(
  null,
  (get, set) => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    
    set(accessTokenAtom, null);
    set(refreshTokenAtom, null);
    set(currentUserAtom, null);
    set(employeeProfileAtom, null);
  }
); 