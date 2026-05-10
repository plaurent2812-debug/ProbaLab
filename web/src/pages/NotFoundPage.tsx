import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';

export default function NotFoundPage() {
  return (
    <div className="mx-auto max-w-md px-6 py-24 text-center space-y-4">
      <h1 className="text-3xl font-bold">404</h1>
      <p className="text-muted-foreground">Cette page n'existe pas.</p>
      <Button asChild><Link to="/">Retour à l'accueil</Link></Button>
    </div>
  );
}
