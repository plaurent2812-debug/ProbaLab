import { motion } from 'framer-motion';
import { ArrowRight, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { EASE_OUT } from './animations';

export function FinalCTA() {
  return (
    <section className="relative mx-auto max-w-6xl px-4 py-20 md:px-8 md:py-32">
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6, ease: EASE_OUT }}
      >
        <Card className="relative overflow-hidden border-white/10 bg-gradient-to-br from-emerald-500/10 via-white/[0.02] to-blue-500/10 p-10 text-center backdrop-blur md:p-16">
          <div
            aria-hidden
            className="pointer-events-none absolute inset-0"
            style={{
              background:
                'radial-gradient(ellipse at center, rgba(16,185,129,0.15) 0%, transparent 60%)',
            }}
          />
          <div className="relative">
            <Badge className="mb-6 gap-1.5 border-emerald-500/30 bg-emerald-500/10 text-emerald-400">
              <Sparkles className="h-3 w-3" />
              14 jours gratuits · Puis 14,99 € / mois
            </Badge>
            <h2 className="mx-auto max-w-2xl text-balance text-4xl font-bold tracking-tight text-white md:text-5xl">
              Arrêtez de parier au feeling.
            </h2>
            <p className="mx-auto mt-5 max-w-xl text-balance text-lg text-slate-400">
              Rejoignez les parieurs qui parient avec des probabilités calibrées. Annulez
              en 1 clic.
            </p>
            <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
              <Button
                asChild
                size="lg"
                className="group gap-2 bg-emerald-500 text-black shadow-[0_0_0_1px_rgba(16,185,129,0.3),0_8px_24px_-8px_rgba(16,185,129,0.6)] transition-all hover:translate-y-[-1px] hover:bg-emerald-400"
              >
                <Link to="/premium">
                  Commencer l'essai gratuit
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
                </Link>
              </Button>
              <Button
                asChild
                size="lg"
                variant="outline"
                className="border-white/10 bg-white/5 text-white hover:bg-white/10"
              >
                <Link to="/premium">Comparer les formules</Link>
              </Button>
            </div>
          </div>
        </Card>
      </motion.div>
    </section>
  );
}
