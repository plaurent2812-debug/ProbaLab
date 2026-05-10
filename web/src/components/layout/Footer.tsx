import { Link } from 'react-router-dom';

export function Footer() {
  return (
    <footer className="border-t border-border bg-background">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-6 text-sm text-muted-foreground">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <p>&copy; 2026 ProbaLab. Plateforme d'analyse probabiliste sportive.</p>
          <nav className="flex flex-wrap gap-4">
            <Link to="/legal/mentions" className="hover:text-foreground">Mentions légales</Link>
            <Link to="/legal/cgu" className="hover:text-foreground">CGU</Link>
            <Link to="/legal/jeu-responsable" className="hover:text-foreground">Jeu responsable</Link>
          </nav>
        </div>
      </div>
    </footer>
  );
}
