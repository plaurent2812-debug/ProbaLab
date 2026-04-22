import { motion } from 'framer-motion';
import { Brain, LineChart, Zap } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { EASE_OUT } from './animations';

const STEPS = [
  {
    icon: Brain,
    title: 'Nos modèles calculent',
    body: '3 couches : Dixon-Coles + ELO, ML calibré (XGBoost), et analyse narrative Gemini. Chaque match → une probabilité réelle.',
  },
  {
    icon: LineChart,
    title: 'On compare aux cotes',
    body: "On croise nos probas avec les cotes de 12+ bookmakers. Si notre proba > proba implicite de la cote, il y a de la value.",
  },
  {
    icon: Zap,
    title: 'On signale les value bets',
    body: 'Seuls les paris avec un edge ≥5% passent le filtre. Vous recevez une alerte, avec la mise Kelly optimale et le meilleur book.',
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
          La même méthode qu'un{' '}
          <em className="not-italic text-emerald-400">quant fund</em>.
          <br />
          Appliquée aux paris sportifs.
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
