import type { ReactNode } from 'react';
import { Header } from './Header';
import { Footer } from './Footer';
import { MobileNav } from './MobileNav';

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground">
      <Header />
      <main className="flex-1 pb-14 md:pb-0">{children}</main>
      <Footer />
      <MobileNav />
    </div>
  );
}
