import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { goalsApi } from '../api/goals';
import type { GoalCreate } from '../types/goals';
import '../styles/Goals.css';

export const GoalFormPage = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id?: string }>();
  const isEditMode = !!id;
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState<Partial<GoalCreate>>({
    title: '',
    description: '',
    expected_results: '',
    start_period: '',
    end_period: ''
  });

  useEffect(() => {
    // If in edit mode, fetch the goal data
    if (isEditMode && id) {
      const fetchGoal = async () => {
        setIsLoading(true);
        try {
          const goalData = await goalsApi.getById(Number(id));
          setFormData({
            title: goalData.title,
            description: goalData.description,
            expected_results: goalData.expected_results,
            start_period: formatDateForInput(goalData.start_period),
            end_period: formatDateForInput(goalData.end_period)
          });
        } catch (error) {
          console.error('Error fetching goal:', error);
          setError('Не удалось загрузить данные цели');
        } finally {
          setIsLoading(false);
        }
      };

      fetchGoal();
    }
  }, [id, isEditMode]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      if (isEditMode && id) {
        await goalsApi.update(Number(id), formData as GoalCreate);
      } else {
        await goalsApi.create(formData as GoalCreate);
      }
      navigate('/goals');
    } catch (error) {
      console.error('Error saving goal:', error);
      setError('Не удалось сохранить цель');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading && isEditMode) {
    return <div>Загрузка данных цели...</div>;
  }

  return (
    <div className="goal-form-container">
      <h1>{isEditMode ? 'Редактирование цели' : 'Создание новой цели'}</h1>
      
      {error && <div className="error-message">{error}</div>}
      
      <form onSubmit={handleSubmit} className="goal-form">
        <div className="form-group">
          <label htmlFor="title">Название цели</label>
          <input
            type="text"
            id="title"
            name="title"
            value={formData.title}
            onChange={handleChange}
            required
            placeholder="Введите название цели"
          />
        </div>

        <div className="form-group">
          <label htmlFor="description">Описание</label>
          <textarea
            id="description"
            name="description"
            value={formData.description}
            onChange={handleChange}
            required
            placeholder="Опишите цель подробно"
            rows={4}
          />
        </div>

        <div className="form-group">
          <label htmlFor="expected_results">Ожидаемые результаты</label>
          <textarea
            id="expected_results"
            name="expected_results"
            value={formData.expected_results}
            onChange={handleChange}
            required
            placeholder="Опишите ожидаемые результаты"
            rows={4}
          />
        </div>

        <div className="form-row">
          <div className="form-group half">
            <label htmlFor="start_period">Дата начала</label>
            <input
              type="date"
              id="start_period"
              name="start_period"
              value={formData.start_period}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-group half">
            <label htmlFor="end_period">Дата окончания</label>
            <input
              type="date"
              id="end_period"
              name="end_period"
              value={formData.end_period}
              onChange={handleChange}
              required
            />
          </div>
        </div>

        <div className="form-actions">
          <button 
            type="button" 
            className="button secondary"
            onClick={() => navigate('/goals')}
          >
            Отмена
          </button>
          <button 
            type="submit" 
            className="button primary"
            disabled={isLoading}
          >
            {isLoading ? 'Сохранение...' : (isEditMode ? 'Обновить' : 'Создать')}
          </button>
        </div>
      </form>
    </div>
  );
};

// Helper function to format date for the input element
const formatDateForInput = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toISOString().split('T')[0]; // Returns YYYY-MM-DD
}; 