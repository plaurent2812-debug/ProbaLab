import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/button';

export default function AccountPage() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();

  async function handleSignOut() {
    await signOut();
    navigate('/auth/login', { replace: true });
  }

  return (
    <div className="mx-auto max-w-2xl px-4 sm:px-6 lg:px-8 py-12 space-y-6">
      <h1 className="text-2xl font-bold">Mon compte</h1>
      <div className="rounded-lg border border-border bg-card p-6 space-y-2">
        <div className="text-sm text-muted-foreground">Email connecté</div>
        <div className="text-base">{user?.email}</div>
      </div>
      <Button variant="outline" onClick={() => void handleSignOut()}>Se déconnecter</Button>
    </div>
  );
}
