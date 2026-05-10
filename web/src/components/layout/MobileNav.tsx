import { NavLink } from 'react-router-dom';
import { Home, User } from 'lucide-react';
import { cn } from '@/lib/cn';
import { useAuth } from '@/hooks/useAuth';

const ITEMS = [
  { to: '/', label: 'Accueil', icon: Home },
];

export function MobileNav() {
  const { user } = useAuth();
  return (
    <nav className="md:hidden fixed bottom-0 inset-x-0 z-40 border-t border-border bg-background/95 backdrop-blur">
      <div className="flex items-stretch justify-around h-14">
        {ITEMS.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              cn(
                'flex-1 flex flex-col items-center justify-center gap-0.5 text-xs',
                isActive ? 'text-foreground' : 'text-muted-foreground'
              )
            }
          >
            <Icon className="h-5 w-5" />
            {label}
          </NavLink>
        ))}
        <NavLink
          to={user ? '/account' : '/auth/login'}
          className={({ isActive }) =>
            cn(
              'flex-1 flex flex-col items-center justify-center gap-0.5 text-xs',
              isActive ? 'text-foreground' : 'text-muted-foreground'
            )
          }
        >
          <User className="h-5 w-5" />
          {user ? 'Compte' : 'Connexion'}
        </NavLink>
      </div>
    </nav>
  );
}
