import { useState } from "react"
import { CheckCircle2, XCircle, Minus } from "lucide-react"
import { cn } from "@/lib/utils"
import { formatOdds, formatProba, formatEV } from "@/lib/statsHelper"
import { ResultBadge, MarketBadge, ConfStars } from "./badges"
import { saveBet, updateBetResult } from "./api"

interface Bet {
    id?: string | number
    label: string
    market: string
    odds: number
    proba_model: number
    proba_bookmaker?: number | null
    confidence: number
    ev?: number | null
    bookmaker?: string | null
    is_value?: boolean
    fixture_id?: string | number
    result?: string
}

interface BetCardProps {
    bet: Bet
    sport: string
    date: string
    isAdmin: boolean
    onResultUpdate?: () => void
}

export function BetCard({ bet, sport, date, isAdmin, onResultUpdate }: BetCardProps) {
    const [updating, setUpdating] = useState(false)
    const [localResult, setLocalResult] = useState(bet.result || "PENDING")
    const [betId, setBetId] = useState<string | number | undefined>(bet.id)
    const [saving, setSaving] = useState(false)

    async function handleSave() {
        setSaving(true)
        try {
            const resp = await saveBet(bet as Record<string, unknown>, sport, date)
            if (resp.id) {
                setBetId(resp.id)
                setLocalResult("PENDING")
            }
        } finally { setSaving(false) }
    }

    async function handleResult(result: string) {
        if (!betId) {
            setSaving(true)
            try {
                const resp = await saveBet(bet as Record<string, unknown>, sport, date)
                if (resp.id) {
                    setBetId(resp.id)
                    setUpdating(true)
                    await updateBetResult(resp.id, result)
                    setLocalResult(result)
                    onResultUpdate?.()
                }
            } finally { setSaving(false); setUpdating(false) }
            return
        }
        setUpdating(true)
        try {
            await updateBetResult(betId, result)
            setLocalResult(result)
            onResultUpdate?.()
        } finally { setUpdating(false) }
    }

    const isTracked = !!betId
    const isBestOdds = bet.odds >= 1.75 && bet.odds <= 2.20

    return (
        <div className={cn(
            "rounded-xl border p-4 transition-all duration-200",
            localResult === "WIN" && "border-emerald-500/30 bg-emerald-500/5",
            localResult === "LOSS" && "border-red-500/20 bg-red-500/5",
            localResult === "PENDING" && "border-border/60 bg-card hover:border-border",
            localResult === "VOID" && "border-slate-500/20 bg-slate-500/5",
        )}>
            <div className="flex items-start justify-between gap-3 mb-2">
                <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-foreground leading-tight">{bet.label}</p>
                    <div className="flex items-center flex-wrap gap-1.5 mt-1.5">
                        <MarketBadge market={bet.market} />
                        {bet.is_value && (
                            <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-amber-500/15 text-amber-400 uppercase tracking-wider">
                                Value
                            </span>
                        )}
                        {isBestOdds && (
                            <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-emerald-500/15 text-emerald-400">
                                Cible
                            </span>
                        )}
                    </div>
                </div>
                <ResultBadge result={localResult} betDate={date} />
            </div>

            <div className="flex items-center justify-between mt-3">
                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    <span className="font-mono font-bold text-foreground text-base">
                        {formatOdds(bet.odds)}
                    </span>
                    <div className="flex flex-col">
                        <span>{formatProba(bet.proba_model)} modele</span>
                        {bet.proba_bookmaker != null && (
                            <span className="text-[10px] text-muted-foreground">
                                {formatProba(bet.proba_bookmaker)} bookmaker
                            </span>
                        )}
                        <ConfStars conf={bet.confidence} />
                    </div>
                    {bet.ev != null && bet.ev > 0 && (
                        <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-emerald-500/15 text-emerald-400">
                            EV {formatEV(bet.ev)}
                        </span>
                    )}
                    {bet.bookmaker && (
                        <span className="text-[9px] text-muted-foreground opacity-60 capitalize">
                            {bet.bookmaker}
                        </span>
                    )}
                </div>

                {isAdmin && (
                    <div className="flex items-center gap-1">
                        {!isTracked && localResult === "PENDING" && (
                            <button
                                onClick={handleSave}
                                disabled={saving}
                                className="px-3 py-1.5 rounded text-[10px] font-bold bg-primary/15 text-primary hover:bg-primary/25 transition-colors disabled:opacity-50"
                            >
                                {saving ? "..." : "Tracker"}
                            </button>
                        )}
                        {(isTracked || localResult !== "PENDING") && (
                            <div className="flex gap-2">
                                <button
                                    onClick={() => handleResult("WIN")}
                                    disabled={updating}
                                    className="w-10 h-10 rounded flex items-center justify-center bg-emerald-500/15 hover:bg-emerald-500/30 transition-colors text-emerald-400 disabled:opacity-50"
                                    title="WIN"
                                >
                                    <CheckCircle2 className="w-4 h-4" />
                                </button>
                                <button
                                    onClick={() => handleResult("LOSS")}
                                    disabled={updating}
                                    className="w-10 h-10 rounded flex items-center justify-center bg-red-500/15 hover:bg-red-500/30 transition-colors text-red-400 disabled:opacity-50"
                                    title="LOSS"
                                >
                                    <XCircle className="w-4 h-4" />
                                </button>
                                <button
                                    onClick={() => handleResult("VOID")}
                                    disabled={updating}
                                    className="w-10 h-10 rounded flex items-center justify-center bg-slate-500/15 hover:bg-slate-500/30 transition-colors text-slate-400 disabled:opacity-50"
                                    title="NUL/VOID"
                                >
                                    <Minus className="w-4 h-4" />
                                </button>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    )
}
