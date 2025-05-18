import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAtom } from 'jotai';
import { setAuthTokensAtom, currentUserAtom, employeeProfileAtom } from '../store/auth';
import { authApi } from '../api/auth';
import type { LoginCredentials } from '../types/auth';

export const LoginPage = () => {
  const navigate = useNavigate();
  const [, setAuthTokens] = useAtom(setAuthTokensAtom);
  const [, setCurrentUser] = useAtom(currentUserAtom);
  const [, setEmployeeProfile] = useAtom(employeeProfileAtom);
  
  const [credentials, setCredentials] = useState<LoginCredentials>({
    username: '',
    password: '',
  });
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setCredentials((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const authResponse = await authApi.login(credentials);
      setAuthTokens(authResponse);

      // Get additional user data if needed
      if (authResponse.has_employee_profile) {
        try {
          const employeeData = await authApi.getEmployeeProfile();
          setEmployeeProfile(employeeData);
        } catch (error) {
          console.error('Failed to fetch employee profile:', error);
        }
      }

      // Set current user from auth response data
      setCurrentUser({
        id: authResponse.user_id,
        username: authResponse.username,
        email: authResponse.email,
        first_name: authResponse.full_name.split(' ')[0] || '',
        last_name: authResponse.full_name.split(' ')[1] || '',
        role: authResponse.role,
      });

      navigate('/dashboard');
    } catch (error) {
      console.error('Login failed:', error);
      setError('Неверное имя пользователя или пароль');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-form-container">
        <h1>Talentum</h1>
        <h2>Вход в систему</h2>
        
        {error && <div className="error-message">{error}</div>}
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="username">Имя пользователя</label>
            <input
              type="text"
              id="username"
              name="username"
              value={credentials.username}
              onChange={handleChange}
              required
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="password">Пароль</label>
            <input
              type="password"
              id="password"
              name="password"
              value={credentials.password}
              onChange={handleChange}
              required
            />
          </div>
          
          <button type="submit" disabled={isLoading}>
            {isLoading ? 'Вход...' : 'Войти'}
          </button>
        </form>
      </div>
    </div>
  );
}; 