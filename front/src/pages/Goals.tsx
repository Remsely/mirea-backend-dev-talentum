import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAtomValue } from 'jotai';
import { isManagerAtom, employeeIdAtom } from '../store/auth';
import { goalsApi } from '../api/goals';
import type { Goal } from '../types/goals';
import type { Employee } from '../types/auth';
import '../styles/Goals.css';
import axiosInstance from '../api/axios';
import { EmployeeCard } from '../components/EmployeeCard';

export const GoalsPage = () => {
  const isManager = useAtomValue(isManagerAtom);
  const employeeId = useAtomValue(employeeIdAtom);

  const [activeTab, setActiveTab] = useState('goals');
  const [goals, setGoals] = useState<Goal[]>([]);
  const [teamGoals, setTeamGoals] = useState<Goal[]>([]);
  const [subordinates, setSubordinates] = useState<Employee[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isTeamLoading, setIsTeamLoading] = useState(true);

  // Загрузка моих целей
  useEffect(() => {
    const fetchGoals = async () => {
      setIsLoading(true);
      try {
        const data = await goalsApi.getMyGoals();
        setGoals(data);
      } catch (error) {
        console.error('Error fetching goals:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchGoals();
  }, []);

  // Загрузка данных команды
  useEffect(() => {
    if (isManager && activeTab === 'team' && employeeId) {
      const fetchTeamData = async () => {
        setIsTeamLoading(true);
        try {
          // Get employee profile with subordinates
          const response = await axiosInstance.get(`/employees/${employeeId}/`);
          const employeeData = response.data;
          setSubordinates(employeeData.subordinates || []);
          
          // Fetch goals for all subordinates
          const allTeamGoals = [];
          for (const subordinate of employeeData.subordinates || []) {
            try {
              const subordinateGoals = await goalsApi.getEmployeeGoals(subordinate.id);
              allTeamGoals.push(...subordinateGoals);
            } catch (error) {
              console.error(`Error fetching goals for employee ${subordinate.id}:`, error);
            }
          }
          setTeamGoals(allTeamGoals);
        } catch (error) {
          // Alternative approach if the direct employee endpoint fails
          try {
            // Try to fetch via the my_team endpoint
            const teamResponse = await axiosInstance.get('/employees/my_team/');
            const subordinatesData = teamResponse.data;
            setSubordinates(subordinatesData || []);
            
            // Fetch goals for all subordinates
            const allTeamGoals = [];
            for (const subordinate of subordinatesData || []) {
              try {
                const subordinateGoals = await goalsApi.getEmployeeGoals(subordinate.id);
                allTeamGoals.push(...subordinateGoals);
              } catch (error) {
                console.error(`Error fetching goals for employee ${subordinate.id}:`, error);
              }
            }
            setTeamGoals(allTeamGoals);
          } catch (teamError) {
            console.error('Error fetching team data:', teamError);
          }
        } finally {
          setIsTeamLoading(false);
        }
      };

      fetchTeamData();
    }
  }, [isManager, activeTab, employeeId]);

  const getStatusBadgeClass = (status: string) => {
    const statusMap: Record<string, string> = {
      draft: 'status-badge-draft',
      pending_approval: 'status-badge-pending',
      approved: 'status-badge-approved',
      in_progress: 'status-badge-progress',
      pending_assessment: 'status-badge-assessment',
      completed: 'status-badge-completed',
      cancelled: 'status-badge-cancelled'
    };
    
    return `status-badge ${statusMap[status] || 'status-badge-default'}`;
  };

  const renderGoalsList = (goalsList: Goal[], showEmployee = false, approvalActions = false) => {
    if (goalsList.length === 0) {
      return (
        <div className="empty-state">
          <p>Целей не найдено.</p>
          {activeTab === 'goals' && (
            <Link to="/goals/new" className="button primary">Создать цель</Link>
          )}
        </div>
      );
    }

    return (
      <div className="goals-list-container">
        <table className="goals-table">
          <colgroup>
            <col style={{ width: 'auto' }} />
            {showEmployee && <col style={{ width: 'auto' }} />}
            <col style={{ width: 'auto' }} />
            <col style={{ width: 'auto' }} />
            <col style={{ width: 'auto' }} />
            <col style={{ width: '1%' }} />
          </colgroup>
          <thead>
            <tr>
              <th>Название</th>
              {showEmployee && <th>Сотрудник</th>}
              <th>Статус</th>
              <th>Начало</th>
              <th>Окончание</th>
              <th>Действия</th>
            </tr>
          </thead>
          <tbody>
            {goalsList.map(goal => (
              <tr key={goal.id}>
                <td>{goal.title}</td>
                {showEmployee && (
                  <td>{goal.employee?.user?.first_name} {goal.employee?.user?.last_name}</td>
                )}
                <td>
                  <span className={getStatusBadgeClass(goal.status)}>
                    {getStatusText(goal.status)}
                  </span>
                </td>
                <td>{formatDate(goal.start_period)}</td>
                <td>{formatDate(goal.end_period)}</td>
                <td className="actions-cell">
                  <div className="actions">
                    <Link to={`/goals/${goal.id}`} className="button small">Просмотр</Link>
                    {activeTab === 'goals' && goal.status === 'draft' && (
                      <Link to={`/goals/${goal.id}/edit`} className="button small secondary">Редактировать</Link>
                    )}
                    {activeTab === 'goals' && goal.status === 'draft' && (
                      <button onClick={() => handleSubmitGoal(goal.id)} className="button small primary">Отправить на согласование</button>
                    )}
                    {approvalActions && goal.status === 'pending_approval' && (
                      <button onClick={() => handleApproveGoal(goal.id)} className="button small primary">Одобрить</button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const renderSubordinatesList = () => {
    if (subordinates.length === 0) {
      return <p>В вашей команде пока нет сотрудников.</p>;
    }

    return (
      <div className="subordinates-list">
        <h3>Моя команда</h3>
        <div className="subordinates-cards">
          {subordinates.map(subordinate => (
            <EmployeeCard key={subordinate.id} employee={subordinate} />
          ))}
        </div>
      </div>
    );
  };

  if (isLoading && activeTab === 'goals') {
    return <div>Загрузка целей...</div>;
  }

  if (isTeamLoading && activeTab === 'team') {
    return <div>Загрузка данных команды...</div>;
  }

  // Фильтрация целей для вкладки "Моя команда"
  const pendingApprovalGoals = teamGoals.filter(goal => goal.status === 'pending_approval');
  const otherTeamGoals = teamGoals.filter(goal => goal.status !== 'pending_approval');

  return (
    <div className="goals-page">
      <div className="header-actions">
        <h1>Цели</h1>
        {activeTab === 'goals' && (
          <Link to="/goals/new" className="button primary">Создать новую цель</Link>
        )}
      </div>

      {isManager && (
        <div className="tabs">
          <button 
            className={`tab ${activeTab === 'goals' ? 'active' : ''}`}
            onClick={() => setActiveTab('goals')}
          >
            Цели
          </button>
          <button 
            className={`tab ${activeTab === 'team' ? 'active' : ''}`}
            onClick={() => setActiveTab('team')}
          >
            Моя команда
          </button>
        </div>
      )}

      {activeTab === 'goals' ? (
        renderGoalsList(goals)
      ) : (
        <div className="team-goals">
          {renderSubordinatesList()}
          
          {pendingApprovalGoals.length > 0 && (
            <div className="pending-goals-section">
              <h3>Цели на согласование</h3>
              {renderGoalsList(pendingApprovalGoals, true, true)}
            </div>
          )}
          
          <div className="other-team-goals-section">
            <h3>Все цели сотрудников</h3>
            {renderGoalsList(otherTeamGoals, true)}
          </div>
        </div>
      )}
    </div>
  );
};

// Helper functions
const getStatusText = (status: string): string => {
  const statusMap: Record<string, string> = {
    draft: 'Черновик',
    pending_approval: 'На согласовании',
    approved: 'Согласовано',
    in_progress: 'В процессе',
    pending_assessment: 'Ожидает оценки',
    completed: 'Завершено',
    cancelled: 'Отменено'
  };
  
  return statusMap[status] || status;
};

const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString('ru-RU');
};

const handleSubmitGoal = async (goalId: number) => {
  try {
    await goalsApi.submit(goalId);
    window.location.reload();
  } catch (error) {
    console.error('Error submitting goal:', error);
    alert('Не удалось отправить цель на согласование');
  }
};

const handleApproveGoal = async (goalId: number) => {
  try {
    await goalsApi.approve(goalId);
    window.location.reload();
  } catch (error) {
    console.error('Error approving goal:', error);
    alert('Не удалось одобрить цель');
  }
}; 