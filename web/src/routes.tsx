import { Routes, Route } from 'react-router-dom';
import { AppShell } from '@/components/layout/AppShell';
import { ProtectedRoute } from '@/components/shared/ProtectedRoute';
import HomePage from '@/pages/HomePage';
import SignupPage from '@/pages/auth/SignupPage';
import LoginPage from '@/pages/auth/LoginPage';
import CallbackPage from '@/pages/auth/CallbackPage';
import AccountPage from '@/pages/account/AccountPage';
import NotFoundPage from '@/pages/NotFoundPage';

export function AppRoutes() {
  return (
    <Routes>
      {/* Auth pages — no shell (full-screen layout) */}
      <Route path="/auth/signup" element={<SignupPage />} />
      <Route path="/auth/login" element={<LoginPage />} />
      <Route path="/auth/callback" element={<CallbackPage />} />

      {/* All other pages — shell wrapped */}
      <Route path="/" element={<AppShell><HomePage /></AppShell>} />
      <Route
        path="/account"
        element={
          <AppShell>
            <ProtectedRoute>
              <AccountPage />
            </ProtectedRoute>
          </AppShell>
        }
      />
      <Route path="*" element={<AppShell><NotFoundPage /></AppShell>} />
    </Routes>
  );
}
