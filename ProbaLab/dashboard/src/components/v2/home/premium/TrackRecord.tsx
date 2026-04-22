import { useState } from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2 } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

// Static curated list for the public landing. Replaced by a live feed
// from /api/public/track-record in a follow-up.
const TRACK_PICKS = [
  { date: '21 avr', match: 'BAR vs CV', pick: '1', odd: 1.45, result: 'win', profit: 45 },
  { date: '20 avr', match: 'BOU vs LEE', pick: '1', odd: 2.1, result: 'win', profit: 110 },
  { date: '19 avr', match: 'MCI vs LIV', pick: 'X2', odd: 2.4, result: 'win', profit: 140 },
  { date: '18 avr', match: 'INT vs MIL', pick: '2', odd: 3.1, result: 'loss', profit: -100 },
  { date: '17 avr', match: 'ATM vs RM', pick: '1', odd: 2.7, result: 'win', profit: 170 },
] as const;

export function TrackRecord() {
  const [tab, setTab] = useState('recent');

  return (
    <section className="mx-auto max-w-6xl px-4 py-16 md:px-8 md:py-24">
      <div className="mb-10 flex items-end justify-between">
        <div>
          <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.2em] text-emerald-400">
            Transparence totale
          </p>
          <h2 className="text-3xl font-bold tracking-tight text-white md:text-4xl">
            Tous nos derniers paris, publics.
          </h2>
          <p className="mt-3 text-slate-400">
            Gagnants ET perdants. Pas de cherry-picking.
          </p>
        </div>
        <Badge
          variant="outline"
          className="hidden border-emerald-500/30 bg-emerald-500/5 text-emerald-400 md:inline-flex"
        >
          <CheckCircle2 className="mr-1.5 h-3 w-3" />
          Audit automatique
        </Badge>
      </div>

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList className="mb-6 bg-white/5">
          <TabsTrigger value="recent">Récents</TabsTrigger>
          <TabsTrigger value="best">Meilleurs</TabsTrigger>
          <TabsTrigger value="worst">Pires</TabsTrigger>
        </TabsList>

        <TabsContent value="recent">
          <Card className="overflow-hidden border-white/5 bg-gradient-to-br from-white/[0.04] to-white/[0.01] backdrop-blur">
            <div className="divide-y divide-white/5">
              {TRACK_PICKS.map((p, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.3, delay: i * 0.05 }}
                  className="flex items-center gap-4 px-5 py-3.5 hover:bg-white/[0.02]"
                >
                  <div className="w-16 shrink-0 text-xs font-medium text-slate-500">{p.date}</div>
                  <div className="flex-1 text-sm font-semibold text-white">{p.match}</div>
                  <Badge
                    variant="outline"
                    className="border-white/10 bg-white/5"
                    style={{ fontVariantNumeric: 'tabular-nums' }}
                  >
                    {p.pick} @ {p.odd}
                  </Badge>
                  <div
                    className={`w-20 text-right text-sm font-bold ${
                      p.result === 'win' ? 'text-emerald-400' : 'text-red-400'
                    }`}
                    style={{ fontVariantNumeric: 'tabular-nums' }}
                  >
                    {p.profit >= 0 ? '+' : ''}
                    {p.profit} €
                  </div>
                  <div
                    className={`h-2 w-2 shrink-0 rounded-full ${
                      p.result === 'win' ? 'bg-emerald-400' : 'bg-red-400'
                    }`}
                    style={{
                      boxShadow: p.result === 'win' ? '0 0 8px #10b981' : '0 0 8px #ef4444',
                    }}
                  />
                </motion.div>
              ))}
            </div>
          </Card>
        </TabsContent>
        <TabsContent value="best">
          <Card className="border-white/5 bg-white/[0.02] p-10 text-center text-slate-500">
            Bientôt disponible — nos meilleurs paris triés par profit.
          </Card>
        </TabsContent>
        <TabsContent value="worst">
          <Card className="border-white/5 bg-white/[0.02] p-10 text-center text-slate-500">
            On assume nos pertes. Liste publique à venir.
          </Card>
        </TabsContent>
      </Tabs>
    </section>
  );
}
