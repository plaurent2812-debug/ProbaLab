import { useState, useEffect } from "react"
import { useNavigate, Link } from "react-router-dom"
import { Star, Search, X, ChevronRight, Trophy, Zap } from "lucide-react"
import { cn } from "@/lib/utils"
import { useWatchlist } from "@/lib/useWatchlist"
import { fetchPredictions } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

function MiniMatchCard({ match, isStarred, onToggleStar }) {
    const navigate = useNavigate()
    const isFinished = ["FT", "AET", "PEN"].includes(match.status)
    const isLive = ["1H", "2H", "HT", "ET", "P", "LIVE"].includes(match.status)
    const pred = match.prediction
    const time = match.date?.slice(11, 16) || "--:--"
    const sport = match.sport || "football"

    return (
        <div
            className="flex items-center gap-3 py-2.5 px-3 hover:bg-accent/40 cursor-pointer border-b border-border/20 last:border-0 transition-colors group"
            onClick={() => navigate(sport === "nhl" ? `/nhl/match/${match.id}` : `/football/match/${match.id}`)}
        >
            {/* Status */}
            <div className="w-12 shrink-0 text-center">
                {isLive ? (
                    <Badge variant="destructive" className="text-[10px] px-1.5 h-5 animate-pulse">
                        {match.elapsed ? `${match.elapsed}'` : "LIVE"}
                    </Badge>
                ) : isFinished ? (
                    <Badge className="text-[10px] px-1.5 h-5 bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-0">FT</Badge>
                ) : (
                    <span className="text-xs font-bold tabular-nums text-foreground/80">{time}</span>
                )}
            </div>

            {/* Teams */}
            <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                    <span className="text-sm font-medium truncate">{match.home_team}</span>
                    {(isFinished || isLive) ? (
                        <span className={cn(
                            "text-sm font-black tabular-nums px-1.5 py-0.5 rounded",
                            isLive ? "text-red-500 bg-red-500/10" : "text-foreground bg-muted/60"
                        )}>
                            {match.home_goals ?? "—"} – {match.away_goals ?? "—"}
                        </span>
                    ) : (
                        <span className="text-xs text-muted-foreground">vs</span>
                    )}
                    <span className="text-sm font-medium truncate text-right">{match.away_team}</span>
                </div>
                {pred?.recommended_bet && !isFinished && (
                    <p className="text-[10px] text-primary/70 mt-0.5">💡 {pred.recommended_bet}</p>
                )}
            </div>

            {/* Star + chevron */}
            <button
                className="shrink-0 p-1 rounded-full hover:bg-amber-500/10 transition-colors"
                onClick={(e) => { e.stopPropagation(); onToggleStar(match.id) }}
            >
                <Star className={cn(
                    "w-4 h-4",
                    isStarred ? "fill-amber-400 text-amber-400" : "text-muted-foreground/30"
                )} />
            </button>
            <ChevronRight className="w-4 h-4 text-muted-foreground/30 group-hover:text-muted-foreground/60 shrink-0" />
        </div>
    )
}

export default function WatchlistPage() {
    const { starredMatches, favTeams, toggleMatch, toggleTeam, isStarred } = useWatchlist()
    const [allMatches, setAllMatches] = useState([])
    const [teamSearch, setTeamSearch] = useState("")
    const [loading, setLoading] = useState(true)

    // Load today's matches to find starred ones and fav team matches
    useEffect(() => {
        const today = new Date().toISOString().slice(0, 10)
        setLoading(true)
        fetchPredictions(today)
            .then(r => setAllMatches(r.matches || []))
            .catch(console.error)
            .finally(() => setLoading(false))
    }, [])

    const starredList = allMatches.filter(m => isStarred(m.id))

    const favTeamMatches = allMatches.filter(m =>
        !isStarred(m.id) && (favTeams.has(m.home_team) || favTeams.has(m.away_team))
    )

    // All unique teams from today's matches for autocomplete
    const allTeams = [...new Set(allMatches.flatMap(m => [m.home_team, m.away_team]))]
        .filter(t => t && t.toLowerCase().includes(teamSearch.toLowerCase()) && !favTeams.has(t))
        .slice(0, 8)

    const hasContent = starredList.length > 0 || favTeams.size > 0

    return (
        <div className="max-w-2xl mx-auto px-4 py-6 space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-xl font-black flex items-center gap-2">
                    <Star className="w-5 h-5 fill-amber-400 text-amber-400" />
                    Mes Favoris
                </h1>
                <p className="text-sm text-muted-foreground mt-0.5">
                    Matchs étoilés et équipes favorites du jour
                </p>
            </div>

            {/* Section: Matchs étoilés */}
            <Card className="border-border/50">
                <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-bold flex items-center gap-2">
                        <Star className="w-4 h-4 fill-amber-400 text-amber-400" />
                        Matchs étoilés
                        {starredList.length > 0 && (
                            <Badge variant="outline" className="ml-auto text-[10px]">
                                {starredList.length}
                            </Badge>
                        )}
                    </CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                    {loading ? (
                        <div className="py-8 text-center">
                            <div className="w-6 h-6 border-2 border-primary/30 border-t-primary rounded-full animate-spin mx-auto" />
                        </div>
                    ) : starredList.length > 0 ? (
                        starredList.map(m => (
                            <MiniMatchCard
                                key={m.id}
                                match={m}
                                isStarred={true}
                                onToggleStar={toggleMatch}
                            />
                        ))
                    ) : (
                        <div className="py-10 text-center text-muted-foreground">
                            <Star className="w-8 h-8 mx-auto mb-2 opacity-20" />
                            <p className="text-sm">Aucun match étoilé aujourd'hui</p>
                            <p className="text-xs mt-1 opacity-60">Clique sur ⭐ dans la liste des matchs</p>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Section: Équipes favorites */}
            <Card className="border-border/50">
                <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-bold flex items-center gap-2">
                        <Trophy className="w-4 h-4 text-primary" />
                        Équipes favorites
                        {favTeams.size > 0 && (
                            <Badge variant="outline" className="ml-auto text-[10px]">
                                {favTeams.size}
                            </Badge>
                        )}
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    {/* Chips */}
                    {favTeams.size > 0 && (
                        <div className="flex flex-wrap gap-2">
                            {[...favTeams].map(team => (
                                <span
                                    key={team}
                                    className="flex items-center gap-1.5 text-xs font-semibold bg-primary/10 text-primary px-2.5 py-1 rounded-full"
                                >
                                    {team}
                                    <button
                                        onClick={() => toggleTeam(team)}
                                        className="hover:text-red-500 transition-colors"
                                    >
                                        <X className="w-3 h-3" />
                                    </button>
                                </span>
                            ))}
                        </div>
                    )}

                    {/* Search to add teams */}
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
                        <input
                            className="w-full text-sm bg-muted/40 border border-border/50 rounded-lg pl-8 pr-3 py-2 outline-none focus:ring-1 focus:ring-primary/30 placeholder:text-muted-foreground"
                            placeholder="Rechercher une équipe..."
                            value={teamSearch}
                            onChange={e => setTeamSearch(e.target.value)}
                        />
                    </div>

                    {/* Autocomplete results */}
                    {teamSearch && allTeams.length > 0 && (
                        <div className="border border-border/50 rounded-lg overflow-hidden">
                            {allTeams.map(team => (
                                <button
                                    key={team}
                                    className="w-full text-left text-sm px-3 py-2 hover:bg-accent/60 border-b border-border/20 last:border-0 transition-colors"
                                    onClick={() => { toggleTeam(team); setTeamSearch("") }}
                                >
                                    + {team}
                                </button>
                            ))}
                        </div>
                    )}

                    {teamSearch && allTeams.length === 0 && (
                        <p className="text-xs text-muted-foreground text-center py-2">
                            Aucune équipe trouvée pour "{teamSearch}"
                        </p>
                    )}

                    {/* Fav team matches today */}
                    {favTeamMatches.length > 0 && (
                        <div>
                            <p className="text-xs font-semibold text-muted-foreground mb-2 flex items-center gap-1">
                                <Zap className="w-3 h-3" /> Matchs de tes équipes aujourd'hui
                            </p>
                            <div className="border border-border/40 rounded-lg overflow-hidden">
                                {favTeamMatches.map(m => (
                                    <MiniMatchCard
                                        key={m.id}
                                        match={m}
                                        isStarred={isStarred(m.id)}
                                        onToggleStar={toggleMatch}
                                    />
                                ))}
                            </div>
                        </div>
                    )}

                    {favTeams.size > 0 && favTeamMatches.length === 0 && !loading && (
                        <p className="text-xs text-muted-foreground text-center py-2">
                            Aucun match de tes équipes favorites aujourd'hui
                        </p>
                    )}

                    {favTeams.size === 0 && !teamSearch && (
                        <p className="text-xs text-muted-foreground text-center py-2">
                            Recherche une équipe pour l'ajouter à tes favoris
                        </p>
                    )}
                </CardContent>
            </Card>

            {/* CTA to matches */}
            <div className="text-center">
                <Button variant="outline" size="sm" asChild>
                    <Link to="/football">Voir tous les matchs Football</Link>
                </Button>
            </div>
        </div>
    )
}
