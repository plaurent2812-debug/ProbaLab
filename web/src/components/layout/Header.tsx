import { Link, NavLink } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/cn';
import { Zap } from 'lucide-react';

const NAV_ITEMS: { to: string; label: string }[] = [
  { to: '/', label: 'Accueil' },
];

export function Header() {
  const { user, signOut } = useAuth();

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 h-14 flex items-center gap-4">
        <Link to="/" className="flex items-center gap-2 font-semibold">
          <Zap className="h-5 w-5 text-primary" />
          <span>ProbaLab</span>
        </Link>

        <nav className="hidden md:flex items-center gap-1 ml-4">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  'rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
                  isActive ? 'bg-muted text-foreground' : 'text-muted-foreground hover:text-foreground'
                )
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="ml-auto flex items-center gap-2">
          {user ? (
            <>
              <span className="hidden sm:inline text-sm text-muted-foreground truncate max-w-[180px]">
                {user.email}
              </span>
              <Button size="sm" variant="outline" onClick={() => void signOut()}>
                Déconnexion
              </Button>
            </>
          ) : (
            <>
              <Button size="sm" variant="ghost" asChild>
                <Link to="/auth/login">Connexion</Link>
              </Button>
              <Button size="sm" asChild>
                <Link to="/auth/signup">Inscription</Link>
              </Button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
