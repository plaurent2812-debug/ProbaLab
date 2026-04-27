import { motion } from 'framer-motion';
import { Brain, LineChart, Zap } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { EASE_OUT } from './animations';

const STEPS = [
  {
    icon: Brain,
    title: 'On analyse chaque match',
    body: 'Forme récente, calendrier, niveau des équipes, contexte et cotes du marché sont transformés en probabilités lisibles.',
  },
  {
    icon: LineChart,
    title: 'On explique les probabilités',
    body: "Vous voyez rapidement l'équipe favorite, le risque du nul, les scénarios probables et les points qui peuvent faire basculer le match.",
  },
  {
    icon: Zap,
    title: 'On propose les meilleurs pronos',
    body: 'Quand le signal est assez solide, ProbaLab recommande un prono clair avec le niveau de confiance et les risques à connaître.',
  },
];

export function HowItWorks() {
  return (
    <section className="mx-auto max-w-6xl px-4 py-16 md:px-8 md:py-24">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.5 }}
        className="mb-12 text-center"
      >
        <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.2em] text-emerald-400">
          Comment ça marche
        </p>
        <h2 className="text-3xl font-bold tracking-tight text-white md:text-5xl">
          Une méthode claire et vérifiable.
          <br />
          Pensée pour les parieurs sportifs.
        </h2>
      </motion.div>

      <div className="grid gap-5 md:grid-cols-3">
        {STEPS.map((step, i) => (
          <motion.div
            key={step.title}
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-10%' }}
            transition={{ duration: 0.6, delay: i * 0.1, ease: EASE_OUT }}
          >
            <Card className="group relative h-full overflow-hidden border-white/5 bg-gradient-to-br from-white/[0.04] to-white/[0.01] p-6 backdrop-blur transition-all hover:border-emerald-500/20 hover:from-emerald-500/5 hover:to-white/[0.01]">
              <div className="mb-5 flex h-11 w-11 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-400 ring-1 ring-emerald-500/20 transition-all group-hover:bg-emerald-500/20">
                <step.icon className="h-5 w-5" />
              </div>
              <div className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-emerald-400">
                Étape {i + 1}
              </div>
              <h3 className="mb-2 text-lg font-bold text-white">{step.title}</h3>
              <p className="text-sm leading-relaxed text-slate-400">{step.body}</p>
            </Card>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
