import { Info } from "lucide-react"
import { cn } from "@/lib/utils"
import { formatWilson } from "./utils"

// ── Accuracy ring (circular progress) ─────────────────────────
export function AccuracyRing({ value, size = 52, strokeWidth = 5 }: { value: number; size?: number; strokeWidth?: number }) {
    const radius = (size - strokeWidth) / 2
    const circumference = 2 * Math.PI * radius
    const offset = circumference - (value / 100) * circumference

    const color = value >= 70
        ? "stroke-emerald-500"
        : value >= 50
            ? "stroke-amber-400"
            : "stroke-red-400"

    return (
        <svg width={size} height={size} className="shrink-0 -rotate-90">
            <circle
                cx={size / 2} cy={size / 2} r={radius}
                className="stroke-secondary"
                strokeWidth={strokeWidth}
                fill="none"
            />
            <circle
                cx={size / 2} cy={size / 2} r={radius}
                className={color}
                strokeWidth={strokeWidth}
                fill="none"
                strokeDasharray={circumference}
                strokeDashoffset={offset}
                strokeLinecap="round"
                style={{ transition: "stroke-dashoffset 1s ease-out" }}
            />
        </svg>
    )
}

// ── Market accuracy card ───────────────────────────────────────
export function MarketCard({
    label,
    accuracy,
    icon: Icon,
    color,
    total,
}: {
    label: string
    accuracy: number
    icon: React.ElementType
    color: string
    total?: number
}) {
    const wilsonLabel = total != null && total > 0 ? formatWilson(accuracy, total) : `${accuracy}%`

    return (
        <div className="flex items-center gap-3 p-3.5 rounded-xl bg-card/50 border border-border/40 hover:border-border/70 transition-colors">
            <div className="relative">
                <AccuracyRing value={accuracy} />
                <span className="absolute inset-0 flex items-center justify-center text-xs font-bold tabular-nums rotate-0">
                    {accuracy}%
                </span>
            </div>
            <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold truncate">{label}</p>
                <div className="flex flex-col gap-0.5 mt-0.5">
                    <div className="flex items-center gap-1">
                        <Icon className={cn("w-3 h-3 shrink-0", color)} />
                        <span className="text-xs text-muted-foreground tabular-nums">{wilsonLabel}</span>
                    </div>
                    {total != null && (
                        <span className="text-xs text-muted-foreground/60">{total} matchs</span>
                    )}
                </div>
            </div>
        </div>
    )
}

// ── Stat tile (header KPIs) ────────────────────────────────────
export function StatTile({ value, label, icon: Icon, accent }: {
    value: string | number
    label: string
    icon: React.ElementType
    accent: string
}) {
    return (
        <div className="flex items-center gap-3 p-4 rounded-xl bg-card/50 border border-border/40">
            <div className={cn("p-2 rounded-lg", accent)}>
                <Icon className="w-5 h-5" />
            </div>
            <div>
                <p className="text-2xl font-black tabular-nums">{value}</p>
                <p className="text-xs text-muted-foreground font-medium">{label}</p>
            </div>
        </div>
    )
}

// ── Inline tooltip ─────────────────────────────────────────────
export function InfoTooltip({ content }: { content: React.ReactNode }) {
    return (
        <div className="group relative inline-flex">
            <Info className="w-3.5 h-3.5 text-muted-foreground cursor-help" />
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-card border border-border rounded-lg shadow-xl text-xs text-muted-foreground w-56 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
                {content}
            </div>
        </div>
    )
}

// ── Custom tooltip for charts ──────────────────────────────────
export function ChartTooltip({ active, payload, label }: {
    active?: boolean
    payload?: Array<{ color: string; name: string; value: number }>
    label?: string
}) {
    if (!active || !payload?.length) return null
    return (
        <div className="rounded-lg border border-border bg-card p-3 shadow-xl">
            <p className="text-xs text-muted-foreground font-medium mb-1">{label}</p>
            {payload.map((p, i) => (
                <p key={i} className="text-sm font-semibold">
                    <span className="inline-block w-2 h-2 rounded-full mr-1.5" style={{ background: p.color }} />
                    {p.name}: <span className="tabular-nums">{p.value}</span>
                </p>
            ))}
        </div>
    )
}
