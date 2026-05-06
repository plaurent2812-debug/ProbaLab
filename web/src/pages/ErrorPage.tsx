import { Button } from '@/components/ui/button';

export default function ErrorPage({ error }: { error?: Error }) {
  return (
    <div className="min-h-screen bg-background text-foreground flex items-center justify-center px-6">
      <div className="max-w-md text-center space-y-4">
        <h1 className="text-2xl font-bold">Une erreur est survenue</h1>
        <p className="text-muted-foreground">
          Quelque chose s'est mal passé. L'équipe a été notifiée.
        </p>
        {error && import.meta.env.DEV && (
          <pre className="text-left text-xs text-muted-foreground bg-card p-3 rounded-md overflow-auto">
            {error.message}
          </pre>
        )}
        <Button onClick={() => window.location.assign('/')}>Retour à l'accueil</Button>
      </div>
    </div>
  );
}
