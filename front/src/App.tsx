import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthLayout, GuestLayout } from './layouts/AuthLayout';
import { MainLayout } from './layouts/MainLayout';
import { LoginPage } from './pages/Login';
import { DashboardPage } from './pages/Dashboard';
import { GoalsPage } from './pages/Goals';
import { GoalFormPage } from './pages/GoalForm';
import { GoalDetailPage } from './pages/GoalDetail';

// Create a client
const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* Public routes */}
          <Route element={<GuestLayout />}>
            <Route path="/login" element={<LoginPage />} />
          </Route>

          {/* Protected routes */}
          <Route element={<AuthLayout />}>
            <Route element={<MainLayout />}>
              <Route path="/dashboard" element={<DashboardPage />} />
              
              {/* Goal management */}
              <Route path="/goals" element={<GoalsPage />} />
              <Route path="/goals/new" element={<GoalFormPage />} />
              <Route path="/goals/:id/edit" element={<GoalFormPage />} />
              <Route path="/goals/:id" element={<GoalDetailPage />} />
              
              {/* Feedback system */}
              <Route path="/feedback/requests/:id" element={<div>Отзыв на цель (будет реализовано)</div>} />
              <Route path="/expertise/pending-evaluation" element={<div>Цели на оценку (будет реализовано)</div>} />
              
              {/* Admin panel */}
              <Route path="/admin" element={<div>Администрирование (будет реализовано)</div>} />
            </Route>
          </Route>

          {/* Redirect to dashboard if authenticated, otherwise to login */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
