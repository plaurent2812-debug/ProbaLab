export default function App() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <main className="mx-auto max-w-2xl px-6 py-16 space-y-6">
        <h1 className="text-3xl font-bold">ProbaLab — Foundation</h1>
        <p className="text-muted-foreground">
          Si vous voyez ce texte avec un fond noir, le fond muted plus clair, et les boutons colorés en dessous, le design system est OK.
        </p>
        <div className="flex flex-wrap gap-3">
          <button className="rounded-md bg-primary px-4 py-2 font-medium text-primary-foreground">Primary</button>
          <button className="rounded-md bg-success px-4 py-2 font-medium text-success-foreground">Success</button>
          <button className="rounded-md bg-warning px-4 py-2 font-medium text-warning-foreground">Warning</button>
          <button className="rounded-md bg-danger px-4 py-2 font-medium text-danger-foreground">Danger</button>
          <div className="rounded-md border border-border bg-card px-4 py-2 text-card-foreground">Card surface</div>
        </div>
      </main>
    </div>
  );
}
