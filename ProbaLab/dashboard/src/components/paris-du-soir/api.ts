import { API_ROOT } from "@/lib/api"

export async function fetchBestBets(date: string, sport: string | null = null) {
    const params = new URLSearchParams({ date })
    if (sport) params.set("sport", sport)
    try {
        const res = await fetch(`${API_ROOT}/api/best-bets?${params}`)
        if (!res.ok) return null
        return res.json()
    } catch { return null }
}

export async function fetchBestBetsStats() {
    try {
        const res = await fetch(`${API_ROOT}/api/best-bets/stats`)
        if (!res.ok) return null
        return res.json()
    } catch { return null }
}

export async function updateBetResult(betId: string | number, result: string, notes = "") {
    const res = await fetch(`${API_ROOT}/api/best-bets/${betId}/result`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ result, notes }),
    })
    return res.json()
}

export async function saveBet(bet: Record<string, unknown>, sport: string, date: string) {
    const res = await fetch(`${API_ROOT}/api/best-bets/save`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...bet, sport, date }),
    })
    return res.json()
}

export async function fetchExpertPicks(date: string, sport: string | null = null) {
    const params = new URLSearchParams({ date })
    if (sport && sport !== "both") params.set("sport", sport)
    try {
        const res = await fetch(`${API_ROOT}/api/expert-picks?${params}`)
        if (!res.ok) return []
        const data = await res.json()
        return data.picks || []
    } catch { return [] }
}

export async function deleteExpertPick(id: string | number) {
    try {
        const res = await fetch(`${API_ROOT}/api/expert-picks/${id}`, { method: "DELETE" })
        return res.ok
    } catch { return false }
}
