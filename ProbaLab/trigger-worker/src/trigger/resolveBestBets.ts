import { schedules } from "@trigger.dev/sdk";

const API_URL = process.env.API_URL || "https://web-production-ff663.up.railway.app";
const CRON_SECRET = process.env.CRON_SECRET || "";

const standardRetry = {
    maxAttempts: 3,
    factor: 1.5,
    minTimeoutInMs: 3000,
    maxTimeoutInMs: 30000,
    randomize: true,
};

/** Helper: generate an array of date strings for the last N days */
function getLastNDays(from: Date, n: number): string[] {
    const dates: string[] = [];
    for (let i = 1; i <= n; i++) {
        const d = new Date(from);
        d.setDate(d.getDate() - i);
        dates.push(d.toISOString().slice(0, 10));
    }
    return dates;
}

const headers = {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${CRON_SECRET}`,
};

async function resolveEndpoint(url: string, date: string, sport: string, label: string): Promise<unknown> {
    try {
        const res = await fetch(url, {
            method: "POST",
            headers,
            body: JSON.stringify({ date, sport }),
        });

        if (!res.ok) {
            console.error(`[${label}] ${date} failed (${res.status})`);
            return null;
        }

        const result = await res.json();
        if (result.resolved_count > 0) {
            console.log(`[${label}] ${date}: resolved ${result.resolved_count}`);
        }
        return result;
    } catch (e) {
        console.error(`[${label}] ${date} error:`, e);
        return null;
    }
}

/**
 * ── Resolve All Bets & Expert Picks ──────────────────────────────────
 * Single schedule at 07:00 UTC (08:00 Paris).
 * Sweeps last 7 days for:
 *   1. Football best bets
 *   2. NHL best bets (with game stats fetch)
 *   3. Football expert picks
 *   4. NHL expert picks
 */
export const resolveAllBets = schedules.task({
    id: "resolve-all-bets",
    cron: "0 7 * * *",   // 07:00 UTC = 08:00 Paris
    retry: standardRetry,
    run: async (payload) => {
        const today = new Date(payload.timestamp).toISOString().slice(0, 10);
        const dates = [today, ...getLastNDays(new Date(payload.timestamp), 7)];
        const results: Record<string, unknown> = {};

        // 1. Football best bets
        console.log("[Resolve] Football best bets...");
        for (const date of dates) {
            results[`football-bets-${date}`] = await resolveEndpoint(
                `${API_URL}/api/best-bets/resolve`, date, "football", "Football Bets"
            );
        }

        // 2. NHL best bets (fetch game stats first, then resolve)
        console.log("[Resolve] NHL best bets...");
        for (const date of dates) {
            // Fetch real player stats first
            try {
                await fetch(`${API_URL}/api/nhl/fetch-game-stats`, {
                    method: "POST",
                    headers,
                    body: JSON.stringify({ date }),
                });
            } catch (e) {
                console.error(`[NHL Stats] ${date} error:`, e);
            }

            results[`nhl-bets-${date}`] = await resolveEndpoint(
                `${API_URL}/api/best-bets/resolve`, date, "nhl", "NHL Bets"
            );
        }

        // 3. Football expert picks
        console.log("[Resolve] Football expert picks...");
        for (const date of dates) {
            results[`football-picks-${date}`] = await resolveEndpoint(
                `${API_URL}/api/expert-picks/resolve`, date, "football", "Expert Football"
            );
        }

        // 4. NHL expert picks
        console.log("[Resolve] NHL expert picks...");
        for (const date of dates) {
            results[`nhl-picks-${date}`] = await resolveEndpoint(
                `${API_URL}/api/expert-picks/resolve`, date, "nhl", "Expert NHL"
            );
        }

        console.log("[Resolve] All done");
        return results;
    },
});
