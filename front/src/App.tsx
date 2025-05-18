import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthLayout, GuestLayout } from './layouts/AuthLayout';
import { MainLayout } from './layouts/MainLayout';
import { LoginPage } from './pages/Login';
import { DashboardPage } from './pages/Dashboard';

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
              <Route path="/goals" element={<div>Мои цели (будет реализовано)</div>} />
              <Route path="/goals/:id" element={<div>Детали цели (будет реализовано)</div>} />
              <Route path="/goals/new" element={<div>Создание цели (будет реализовано)</div>} />
              <Route path="/goals/pending-approval" element={<div>Цели на согласование (будет реализовано)</div>} />
              <Route path="/team" element={<div>Моя команда (будет реализовано)</div>} />
              <Route path="/feedback/requests/:id" element={<div>Отзыв на цель (будет реализовано)</div>} />
              <Route path="/expertise/pending-evaluation" element={<div>Цели на оценку (будет реализовано)</div>} />
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
