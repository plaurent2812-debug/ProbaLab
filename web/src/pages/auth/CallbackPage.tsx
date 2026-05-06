import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { FullPageSpinner } from '@/components/shared/LoadingSpinner';

export default function CallbackPage() {
  const { loading, user } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();

  useEffect(() => {
    if (loading) return;
    const next = params.get('next') ?? '/account';
    navigate(user ? next : '/auth/login', { replace: true });
  }, [loading, user, navigate, params]);

  return <FullPageSpinner />;
}
