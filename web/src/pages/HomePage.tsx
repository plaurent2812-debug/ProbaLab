import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/hooks/useAuth';

export default function HomePage() {
  const { user } = useAuth();
  return (
    <div className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8 py-16">
      <div className="space-y-6 text-center">
        <h1 className="text-4xl sm:text-5xl font-bold tracking-tight">
          Probabilités sportives, calculées par IA.
        </h1>
        <p className="text-lg text-muted-foreground">
          Foot et NHL. 8 ligues. Probas par marché, picks du jour, performance vérifiable.
        </p>
        <div className="flex justify-center gap-3">
          {user ? (
            <Button asChild size="lg"><Link to="/account">Mon compte</Link></Button>
          ) : (
            <>
              <Button asChild size="lg"><Link to="/auth/signup">Créer un compte gratuit</Link></Button>
              <Button asChild size="lg" variant="outline"><Link to="/auth/login">Se connecter</Link></Button>
            </>
          )}
        </div>
        <p className="text-xs text-muted-foreground pt-8">
          V2 en construction · Foundation P1 — pages métier livrées en P2.
        </p>
      </div>
    </div>
  );
}
