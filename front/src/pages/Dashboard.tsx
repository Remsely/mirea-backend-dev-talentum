import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAtomValue } from 'jotai';
import { currentUserAtom, isManagerAtom, isExpertiseLeaderAtom } from '../store/auth';
import { goalsApi } from '../api/goals';
import { feedbackApi } from '../api/feedback';
import type { Goal } from '../types/goals';
import type { FeedbackRequestDetail } from '../types/feedback';
import '../styles/Dashboard.css';

export const DashboardPage = () => {
  const currentUser = useAtomValue(currentUserAtom);
  const isManager = useAtomValue(isManagerAtom);
  const isExpertiseLeader = useAtomValue(isExpertiseLeaderAtom);
  
  const [myGoals, setMyGoals] = useState<Goal[]>([]);
  const [pendingApprovalGoals, setPendingApprovalGoals] = useState<Goal[]>([]);
  const [pendingFeedbackRequests, setPendingFeedbackRequests] = useState<FeedbackRequestDetail[]>([]);
  const [pendingExpertEvaluations, setPendingExpertEvaluations] = useState<number[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      setIsLoading(true);
      try {
        // Fetch user's goals
        const goals = await goalsApi.getMyGoals();
        setMyGoals(goals);

        // If user is a manager, fetch goals pending approval
        if (isManager) {
          const pendingGoals = await goalsApi.getPendingApprovalGoals();
          setPendingApprovalGoals(pendingGoals);
        }

        // Fetch feedback requests pending response
        const feedbackRequests = await feedbackApi.getPendingFeedbackRequests();
        setPendingFeedbackRequests(feedbackRequests);

        // If user is an expertise leader, fetch goals pending expert evaluation
        if (isExpertiseLeader) {
          const pendingEvaluations = await feedbackApi.getGoalsPendingExpertEvaluation();
          setPendingExpertEvaluations(pendingEvaluations);
        }
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboardData();
  }, [isManager, isExpertiseLeader]);

  if (isLoading) {
    return <div>Загрузка...</div>;
  }

  return (
    <div className="dashboard-container">
      <h1>Добро пожаловать, {currentUser?.first_name}!</h1>
      
      <div className="dashboard-section">
        <h2>Мои цели</h2>
        {myGoals.length > 0 ? (
          <div className="goals-list">
            {myGoals.map((goal) => (
              <div key={goal.id} className="goal-card">
                <h3>{goal.title}</h3>
                <p>Статус: {getStatusText(goal.status)}</p>
                <p>Срок: {formatDate(goal.end_period)}</p>
                <Link to={`/goals/${goal.id}`}>Подробнее</Link>
              </div>
            ))}
          </div>
        ) : (
          <p>У вас пока нет целей. <Link to="/goals/new">Создать новую цель</Link></p>
        )}
      </div>
      
      {isManager && pendingApprovalGoals.length > 0 && (
        <div className="dashboard-section">
          <h2>Цели на согласование</h2>
          <div className="goals-list">
            {pendingApprovalGoals.map((goal) => (
              <div key={goal.id} className="goal-card">
                <h3>{goal.title}</h3>
                <p>Сотрудник: {goal.employee.user.first_name} {goal.employee.user.last_name}</p>
                <p>Срок: {formatDate(goal.end_period)}</p>
                <Link to={`/goals/${goal.id}`}>Рассмотреть</Link>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {pendingFeedbackRequests.length > 0 && (
        <div className="dashboard-section">
          <h2>Запросы на отзыв</h2>
          <div className="feedback-requests-list">
            {pendingFeedbackRequests.map((request) => (
              <div key={request.id} className="feedback-request-card">
                <h3>{request.goal.title}</h3>
                <p>От: {request.requested_by.user.first_name} {request.requested_by.user.last_name}</p>
                <p>Дата запроса: {formatDate(request.created_dttm)}</p>
                <Link to={`/feedback/requests/${request.id}`}>Оставить отзыв</Link>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {isExpertiseLeader && pendingExpertEvaluations.length > 0 && (
        <div className="dashboard-section">
          <h2>Цели, ожидающие итоговой оценки</h2>
          <p>Количество: {pendingExpertEvaluations.length}</p>
          <Link to="/expertise/pending-evaluation">Перейти к оценке</Link>
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