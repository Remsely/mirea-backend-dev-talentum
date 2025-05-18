import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAtomValue } from 'jotai';
import { currentUserAtom, isManagerAtom } from '../store/auth';
import { goalsApi } from '../api/goals';
import type { Goal, Progress } from '../types/goals';
import '../styles/Goals.css';

export const GoalDetailPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const currentUser = useAtomValue(currentUserAtom);
  const isManager = useAtomValue(isManagerAtom);
  
  const [goal, setGoal] = useState<Goal | null>(null);
  const [progressText, setProgressText] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchGoalDetails = async () => {
      if (!id) return;
      
      setIsLoading(true);
      try {
        const goalData = await goalsApi.getById(Number(id));
        setGoal(goalData);
      } catch (error) {
        console.error('Error fetching goal details:', error);
        setError('Не удалось загрузить информацию о цели');
      } finally {
        setIsLoading(false);
      }
    };

    fetchGoalDetails();
  }, [id]);

  const handleAddProgress = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !progressText.trim()) return;
    
    setIsSubmitting(true);
    setError(null);
    
    try {
      await goalsApi.addProgress(Number(id), {
        description: progressText,
        created_dttm: new Date().toISOString()
      });
      
      // Refresh goal data to show the new progress entry
      const updatedGoal = await goalsApi.getById(Number(id));
      
      // Убедимся, что прогресс отображается в консоли для отладки
      console.log('Обновленные данные цели:', updatedGoal);
      console.log('Записи о прогрессе:', updatedGoal.progress_updates || updatedGoal.progress_entries || []);
      
      setGoal(updatedGoal);
      setProgressText('');
    } catch (error) {
      console.error('Error adding progress:', error);
      setError('Не удалось добавить запись о прогрессе');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmitGoal = async () => {
    if (!id) return;
    
    setIsSubmitting(true);
    try {
      await goalsApi.submit(Number(id));
      // Reload goal data after submission
      const updatedGoal = await goalsApi.getById(Number(id));
      setGoal(updatedGoal);
    } catch (error) {
      console.error('Error submitting goal:', error);
      setError('Не удалось отправить цель на согласование');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleApproveGoal = async () => {
    if (!id) return;
    
    setIsSubmitting(true);
    try {
      await goalsApi.approve(Number(id));
      // Reload goal data after approval
      const updatedGoal = await goalsApi.getById(Number(id));
      setGoal(updatedGoal);
    } catch (error) {
      console.error('Error approving goal:', error);
      setError('Не удалось одобрить цель');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCompleteGoal = async () => {
    if (!id) return;
    
    setIsSubmitting(true);
    try {
      await goalsApi.complete(Number(id));
      // Reload goal data after completion
      const updatedGoal = await goalsApi.getById(Number(id));
      setGoal(updatedGoal);
    } catch (error) {
      console.error('Error completing goal:', error);
      setError('Не удалось завершить цель');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return <div>Загрузка информации о цели...</div>;
  }

  if (error && !goal) {
    return (
      <div className="error-container">
        <p>{error}</p>
        <button onClick={() => navigate('/goals')} className="button">
          Вернуться к списку целей
        </button>
      </div>
    );
  }

  if (!goal) {
    return <div>Цель не найдена</div>;
  }

  const isGoalOwner = currentUser?.id === goal.employee.user.id;
  const canAddProgress = goal.status === 'in_progress' && isGoalOwner;
  const canSubmit = goal.status === 'draft' && isGoalOwner;
  const canApprove = goal.status === 'pending_approval' && isManager;
  const canComplete = goal.status === 'in_progress' && isGoalOwner;

  return (
    <div className="goal-detail-page">
      <div className="header-actions">
        <h1>{goal.title}</h1>
        <div className="actions">
          <button onClick={() => navigate('/goals')} className="button">
            Назад к списку
          </button>
          {canSubmit && (
            <button
              onClick={handleSubmitGoal}
              className="button primary"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Отправка...' : 'Отправить на согласование'}
            </button>
          )}
          {canApprove && (
            <button
              onClick={handleApproveGoal}
              className="button primary"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Одобрение...' : 'Одобрить цель'}
            </button>
          )}
          {canComplete && (
            <button
              onClick={handleCompleteGoal}
              className="button primary"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Завершение...' : 'Завершить цель'}
            </button>
          )}
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="goal-status">
        <span className={`status-badge status-badge-${goal.status}`}>
          {getStatusText(goal.status)}
        </span>
      </div>

      <div className="goal-info">
        <div className="info-section">
          <h2>Детали цели</h2>
          <div className="info-row">
            <div className="info-label">Период:</div>
            <div className="info-value">
              {formatDate(goal.start_period)} - {formatDate(goal.end_period)}
            </div>
          </div>
          <div className="info-row">
            <div className="info-label">Сотрудник:</div>
            <div className="info-value">
              {goal.employee.user.first_name} {goal.employee.user.last_name}
            </div>
          </div>
          <div className="info-row">
            <div className="info-label">Должность:</div>
            <div className="info-value">{goal.employee.position}</div>
          </div>
        </div>

        <div className="info-section">
          <h2>Описание</h2>
          <p>{goal.description}</p>
        </div>

        <div className="info-section">
          <h2>Ожидаемые результаты</h2>
          <p>{goal.expected_results}</p>
        </div>

        <div className="info-section">
          <h2>Прогресс</h2>
          {((goal.progress_updates && goal.progress_updates.length > 0) || (goal.progress_entries && goal.progress_entries.length > 0)) ? (
            <div className="progress-list">
              {(goal.progress_updates || goal.progress_entries || []).map((entry: Progress) => (
                <div key={entry.id} className="progress-entry">
                  <div className="progress-date">{formatDate(entry.created_dttm)}</div>
                  <div className="progress-description">{entry.description}</div>
                </div>
              ))}
            </div>
          ) : (
            <p className="no-items">Пока нет записей о прогрессе</p>
          )}

          {canAddProgress && (
            <div className="add-progress-section">
              <h3>Добавить прогресс</h3>
              <form onSubmit={handleAddProgress}>
                <textarea
                  value={progressText}
                  onChange={e => setProgressText(e.target.value)}
                  placeholder="Опишите прогресс по достижению цели"
                  rows={4}
                  required
                />
                <button
                  type="submit"
                  className="button primary"
                  disabled={isSubmitting || !progressText.trim()}
                >
                  {isSubmitting ? 'Добавление...' : 'Добавить'}
                </button>
              </form>
            </div>
          )}
        </div>
      </div>
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