import { useEffect } from 'react';
import { useAtom, useAtomValue } from 'jotai';
import { 
  accessTokenAtom, 
  currentUserAtom, 
  employeeProfileAtom, 
  isAuthenticatedAtom 
} from '../store/auth';
import { authApi } from '../api/auth';

export const useAuth = () => {
  const isAuthenticated = useAtomValue(isAuthenticatedAtom);
  const accessToken = useAtomValue(accessTokenAtom);
  const [currentUser, setCurrentUser] = useAtom(currentUserAtom);
  const [employeeProfile, setEmployeeProfile] = useAtom(employeeProfileAtom);

  useEffect(() => {
    // If authenticated but no user data, fetch it
    const loadUserData = async () => {
      if (isAuthenticated && accessToken && !currentUser) {
        try {
          const userData = await authApi.getCurrentUser();
          setCurrentUser(userData);

          try {
            const employeeData = await authApi.getEmployeeProfile();
            setEmployeeProfile(employeeData);
          } catch (error) {
            console.error('Failed to load employee profile:', error);
          }
        } catch (error) {
          console.error('Failed to load user data:', error);
        }
      }
    };

    loadUserData();
  }, [isAuthenticated, accessToken, currentUser, setCurrentUser, setEmployeeProfile]);

  return {
    isAuthenticated,
    currentUser,
    employeeProfile
  };
}; 