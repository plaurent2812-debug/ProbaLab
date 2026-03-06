import { schedules } from "@trigger.dev/sdk";

const API_URL = process.env.API_URL || "https://web-production-ff663.up.railway.app";
const CRON_SECRET = process.env.CRON_SECRET || "super_secret_probalab_2026";

const standardRetry = {
    maxAttempts: 3,
    factor: 1.5,
    minTimeoutInMs: 3000,
    maxTimeoutInMs: 30000,
    randomize: true,
};

/**
 * ── Resolve Football Best Bets ─────────────────────────────────────
 * Runs at 07:30 Paris (06:30 UTC) — all European matches from prior
 * day are finished by then. Checks fixtures table for FT results and
 * updates best_bets with WIN / LOSS / VOID automatically.
 */
export const resolveFootballBets = schedules.task({
    id: "resolve-football-bets",
    cron: "30 6 * * *",   // 06:30 UTC = 07:30 Paris
    retry: standardRetry,
    run: async (payload) => {
        const yesterday = new Date(payload.timestamp);
        yesterday.setDate(yesterday.getDate() - 1);
        const date = yesterday.toISOString().slice(0, 10);

        console.log(`[Football Resolve] Checking bets for ${date}`);

        const res = await fetch(`${API_URL}/api/best-bets/resolve`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${CRON_SECRET}`,
            },
            body: JSON.stringify({ date, sport: "football" }),
        });

        if (!res.ok) {
            const text = await res.text();
            throw new Error(`Football resolve failed (${res.status}): ${text}`);
        }

        const result = await res.json();
        console.log(`[Football Resolve] Done:`, result);
        return result;
    },
});

/**
 * ── Resolve NHL Best Bets ──────────────────────────────────────────
 * Runs at 12:00 Paris (11:00 UTC) — all North American NHL games
 * from the prior night are finished (latest ~04:30 Paris).
 * Checks nhl_fixtures for FT scores and resolves player point bets.
 */
export const resolveNHLBets = schedules.task({
    id: "resolve-nhl-bets",
    cron: "0 11 * * *",   // 11:00 UTC = 12:00 Paris
    retry: standardRetry,
    run: async (payload) => {
        // NHL matches listed for date D are played during night D→D+1
        // so at noon we look at "yesterday" which was game night
        const yesterday = new Date(payload.timestamp);
        yesterday.setDate(yesterday.getDate() - 1);
        const date = yesterday.toISOString().slice(0, 10);

        console.log(`[NHL Resolve] Checking bets for game night ${date}`);

        const res = await fetch(`${API_URL}/api/best-bets/resolve`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${CRON_SECRET}`,
            },
            body: JSON.stringify({ date, sport: "nhl" }),
        });

        if (!res.ok) {
            const text = await res.text();
            throw new Error(`NHL resolve failed (${res.status}): ${text}`);
        }

        const result = await res.json();
        console.log(`[NHL Resolve] Done:`, result);
        return result;
    },
});
