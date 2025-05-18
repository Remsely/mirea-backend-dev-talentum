import { Outlet, Link, useNavigate } from 'react-router-dom';
import { useAtom, useAtomValue } from 'jotai';
import { 
  currentUserAtom, 
  employeeProfileAtom, 
  clearAuthAtom,
  isManagerAtom,
  isExpertiseLeaderAtom,
  isAdminAtom
} from '../store/auth';
import { useAuth } from '../hooks/useAuth';

export const MainLayout = () => {
  // Use useAuth hook to ensure user data is loaded
  useAuth();
  
  const navigate = useNavigate();
  const currentUser = useAtomValue(currentUserAtom);
  const employeeProfile = useAtomValue(employeeProfileAtom);
  const isManager = useAtomValue(isManagerAtom);
  const isExpertiseLeader = useAtomValue(isExpertiseLeaderAtom);
  const isAdmin = useAtomValue(isAdminAtom);
  const [, clearAuth] = useAtom(clearAuthAtom);
  
  const handleLogout = () => {
    clearAuth();
    navigate('/login');
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="logo">Talentum</div>
        <div className="user-info">
          {currentUser && (
            <>
              <span>{currentUser.first_name} {currentUser.last_name}</span>
              {employeeProfile && (
                <span className="position">{employeeProfile.position}</span>
              )}
              <button onClick={handleLogout}>Выйти</button>
            </>
          )}
        </div>
      </header>
      
      <div className="app-body">
        <nav className="sidebar">
          <ul>
            <li>
              <Link to="/dashboard">Главная</Link>
            </li>
            <li>
              <Link to="/goals">Мои цели</Link>
            </li>
            {isManager && (
              <li>
                <Link to="/team">Моя команда</Link>
              </li>
            )}
            {isManager && (
              <li>
                <Link to="/goals/pending-approval">На согласование</Link>
              </li>
            )}
            {isExpertiseLeader && (
              <li>
                <Link to="/expertise/pending-evaluation">Ожидают оценки</Link>
              </li>
            )}
            {isAdmin && (
              <li>
                <Link to="/admin">Администрирование</Link>
              </li>
            )}
          </ul>
        </nav>
        
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}; 