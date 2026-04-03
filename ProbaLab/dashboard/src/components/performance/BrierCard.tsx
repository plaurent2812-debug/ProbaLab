import { Activity } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import { InfoTooltip } from "./ui"

interface BrierCardProps {
    score: number
}

export function BrierCard({ score }: BrierCardProps) {
    const { label, className } = score < 0.19
        ? { label: "Excellent", className: "text-emerald-400" }
        : score < 0.21
            ? { label: "Bon", className: "text-amber-400" }
            : score < 0.23
                ? { label: "Acceptable", className: "text-orange-400" }
                : { label: "A ameliorer", className: "text-red-400" }

    const pct = Math.min(100, (score / 0.33) * 100)

    return (
        <Card className="bg-card/50 border-border/50">
            <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-sm">
                    <Activity className="w-4 h-4 text-primary" />
                    Calibration des probabilites
                    <InfoTooltip content={
                        <>
                            <strong className="text-foreground block mb-1">Brier Score normalise</strong>
                            Mesure la precision des probabilites predites (pas seulement le bon/mauvais resultat).
                            <br /><br />
                            <span className="text-emerald-400">{"< 0.19"} = Excellent</span><br />
                            <span className="text-amber-400">{"< 0.21"} = Bon</span><br />
                            <span className="text-orange-400">{"< 0.23"} = Acceptable</span><br />
                            <span className="text-red-400">{"≥ 0.23"} = A ameliorer</span><br /><br />
                            Reference : 0 = parfait, 0.33 = tirage aleatoire.
                        </>
                    } />
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className="flex items-end gap-4">
                    <div>
                        <p className={cn("text-4xl font-black tabular-nums", className)}>
                            {score.toFixed(3)}
                        </p>
                        <p className={cn("text-sm font-semibold mt-1", className)}>{label}</p>
                    </div>
                    <div className="flex-1 mb-2">
                        <div className="flex justify-between text-[10px] text-muted-foreground mb-1">
                            <span>0 (parfait)</span>
                            <span>0.33 (aleatoire)</span>
                        </div>
                        <div className="h-2.5 rounded-full bg-secondary overflow-hidden">
                            <div
                                className={cn(
                                    "h-full rounded-full transition-all duration-1000",
                                    score < 0.19 ? "bg-emerald-500"
                                        : score < 0.21 ? "bg-amber-400"
                                            : score < 0.23 ? "bg-orange-400"
                                                : "bg-red-400"
                                )}
                                style={{ width: `${pct}%` }}
                            />
                        </div>
                        <div className="flex justify-end mt-1">
                            <span className="text-[10px] text-muted-foreground">{(pct).toFixed(0)}% du plafond</span>
                        </div>
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}
