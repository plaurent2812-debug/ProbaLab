import { Lock, Trophy } from "lucide-react"

export function PremiumLock() {
    return (
        <div className="flex flex-col items-center justify-center py-24 px-6 text-center">
            <div className="w-16 h-16 rounded-2xl bg-amber-500/15 flex items-center justify-center mb-5 border border-amber-500/20">
                <Lock className="w-7 h-7 text-amber-400" />
            </div>
            <h2 className="text-lg font-bold mb-2">Acces Premium requis</h2>
            <p className="text-muted-foreground text-sm max-w-sm mb-6">
                Les <strong>Pronos du Jour</strong> — selection quotidienne des 5 meilleurs pronos ⚽ + 🏒 —
                sont reserves aux abonnes Premium.
            </p>
            <a
                href="/premium"
                className="px-5 py-2.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-black font-bold text-sm transition-colors"
            >
                <Trophy className="w-4 h-4 inline mr-1.5" />
                Passer a Premium
            </a>
        </div>
    )
}
