import { task, wait, schedules } from "@trigger.dev/sdk/v3";

const CRON_SECRET = process.env.CRON_SECRET || "super_secret_probalab_2026";
const API_URL = process.env.API_URL || "https://web-production-ff663.up.railway.app";

const standardRetry = {
    maxAttempts: 3,
    factor: 1.5,
    minTimeoutInMs: 2000,
    maxTimeoutInMs: 30000,
    randomize: true,
};


// ─── Task 1: Monitor Halftime (48 min) ─────────────────────────
export const monitorHalftime = task({
    id: "monitor-halftime",

    retry: standardRetry,
    run: async (payload: { fixture_id: string; start_date: string }) => {
        const startTime = new Date(payload.start_date);

        // Wait until 48 minutes after kickoff (halftime buffer)
        const halftimeTime = new Date(startTime.getTime() + 48 * 60 * 1000);

        await wait.until({ date: halftimeTime });

        // Wake up and call Python backend
        const res = await fetch(`${API_URL}/api/trigger/analyze-halftime`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${CRON_SECRET}`
            },
            body: JSON.stringify({ fixture_id: payload.fixture_id }),
        });

        if (!res.ok) {
            throw new Error(`Analyze halftime failed: ${res.statusText}`);
        }

        const data = await res.json();
        return data;
    },
});

// ─── Task 2: Monitor 70th Minute ────────────────────────────────
export const monitor70thMinute = task({
    id: "monitor-70th-minute",

    retry: standardRetry,
    run: async (payload: { fixture_id: string; start_date: string }) => {
        const startTime = new Date(payload.start_date);
        const seventyMinTime = new Date(startTime.getTime() + 70 * 60 * 1000);

        await wait.until({ date: seventyMinTime });

        const res = await fetch(`${API_URL}/api/trigger/analyze-halftime`, { // Assuming same endpoint for now
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${CRON_SECRET}`
            },
            body: JSON.stringify({ fixture_id: payload.fixture_id }),
        });

        if (!res.ok) {
            throw new Error(`Analyze 70th minute failed: ${res.statusText}`);
        }

        return await res.json();
    },
});

// ─── Task 3: Schedule Daily Matches & NHL Eval (CRON 08:00) ──────────────
export const scheduleDailyMatches = schedules.task({
    id: "schedule-daily-matches",

    retry: standardRetry,
    cron: "0 8 * * *",
    run: async () => {
        // 1. NHL Evaluate
        const nhlRes = await fetch(`${API_URL}/api/trigger/nhl-evaluate-performance`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${CRON_SECRET}`
            },
        });
        if (!nhlRes.ok) console.error(`NHL evaluation failed: ${nhlRes.statusText}`);

        const res = await fetch(`${API_URL}/api/trigger/daily-matches`, {
            headers: { "Authorization": `Bearer ${CRON_SECRET}` }
        });
        if (!res.ok) {
            throw new Error(`Failed to fetch daily matches: ${res.statusText}`);
        }
        const data = await res.json();
        const matches = data.matches || [];

        // Schedule both halftime AND 70th minute monitors for each match
        const triggerPromises = matches.flatMap((match: any) => [
            monitorHalftime.trigger({
                fixture_id: match.id,
                start_date: match.date,
            }),
            monitor70thMinute.trigger({
                fixture_id: match.id,
                start_date: match.date,
            }),
        ]);

        await Promise.all(triggerPromises);

        return { scheduled: matches.length, tasks_created: matches.length * 2 };
    },
});

// ─── Task 4: Global Minutely Scheduler (Live Scores & Momentum) ───
export const globalMinutelyScheduler = schedules.task({
    id: "global-minutely-scheduler",

    retry: standardRetry,
    cron: "* * * * *",  // Every 1 min, 24/7
    run: async () => {
        const now = new Date();
        const hour = now.getUTCHours();
        const min = now.getUTCMinutes();

        let promises: Promise<Response>[] = [];

        // 1. Football Live Scores (11h-23h UTC)
        if (hour >= 11 && hour <= 23) {
            promises.push(
                fetch(`${API_URL}/api/trigger/update-live-scores`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${CRON_SECRET}`
                    }
                })
            );
        }

        // 2. Football Momentum (Every 5 mins)
        if (min % 5 === 0) {
            promises.push(
                fetch(`${API_URL}/api/trigger/football-momentum`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${CRON_SECRET}`
                    }
                })
            );
        }

        // 3. NHL Live Scores (16h-08h UTC) => hour >= 16 || hour <= 8
        if (hour >= 16 || hour <= 8) {
            promises.push(
                fetch(`${API_URL}/api/trigger/nhl-update-live-scores`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${CRON_SECRET}`
                    }
                })
            );
        }

        await Promise.allSettled(promises);
        return { scheduled_jobs_ran: promises.length };
    },
});

// ─── Task 4b: Fetch H-1 Lineups (CRON every 15 min, 10h-22h UTC) ──
export const fetchLineups = schedules.task({
    id: "fetch-lineups",

    retry: standardRetry,
    cron: "*/15 10-22 * * *",  // Every 15 min to catch H-1 for any kickoff
    run: async () => {
        const res = await fetch(`${API_URL}/api/trigger/fetch-lineups`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${CRON_SECRET}`
            },
        });

        if (!res.ok) {
            throw new Error(`Fetch lineups failed: ${res.statusText}`);
        }

        return await res.json();
    },
});

// ─── Task 5: Run Daily Pipeline & Reflection (CRON 06:00) ──────────────────
export const runDailyPipeline = schedules.task({
    id: "run-daily-pipeline",

    retry: standardRetry,
    cron: "0 6 * * *",  // Every day at 06:00 UTC
    run: async () => {
        // 1. Run Reflection Engine First
        const reflectionRes = await fetch(`${API_URL}/api/trigger/run-reflection`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${CRON_SECRET}`
            },
        });

        if (!reflectionRes.ok) {
            console.error(`Reflection failed: ${reflectionRes.statusText}`);
            // We do not throw to ensure the pipeline still runs
        }

        // 2. Run Daily Pipeline
        const res = await fetch(`${API_URL}/api/trigger/run-daily-pipeline`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${CRON_SECRET}`
            },
        });

        if (!res.ok) {
            throw new Error(`Pipeline failed: ${res.statusText}`);
        }

        return await res.json();
    },
});

// ─── Task 6: Detect Value Bets (Football & NHL) ───────────────────
export const detectValueBets = schedules.task({
    id: "detect-value-bets",

    retry: standardRetry,
    cron: "0 10,15 * * *",  // Runs at 10:00 (Football) and 15:00 (NHL)
    run: async () => {
        const hour = new Date().getUTCHours();
        let endpoint = "detect-value-bets"; // Football

        if (hour === 15) {
            endpoint = "nhl-value-bets";
        }

        const res = await fetch(`${API_URL}/api/trigger/${endpoint}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${CRON_SECRET}`
            },
        });

        if (!res.ok) {
            throw new Error(`Value bet detection failed: ${res.statusText}`);
        }

        return await res.json();
    },
});

// ─── Task 7: Daily Recap (CRON 23:30) ─────────────────────────
export const dailyRecap = schedules.task({
    id: "daily-recap",

    retry: standardRetry,
    cron: "30 23 * * *",  // Every day at 23:30 UTC
    run: async () => {
        const res = await fetch(`${API_URL}/api/trigger/daily-recap`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${CRON_SECRET}`
            },
        });

        if (!res.ok) {
            throw new Error(`Daily recap failed: ${res.statusText}`);
        }

        return await res.json();
    },
});

// =============================================================================
// NHL TASKS
// =============================================================================

// ─── Task 8: NHL Pipeline (CRON 09:00 UTC = 10h Paris) ────────
export const nhlRunPipeline = schedules.task({
    id: "nhl-run-pipeline",

    retry: standardRetry,
    cron: "0 9 * * *",  // 09:00 UTC = 10h Paris
    run: async () => {
        const res = await fetch(`${API_URL}/api/trigger/nhl-run-pipeline`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${CRON_SECRET}`
            },
        });

        if (!res.ok) {
            throw new Error(`NHL pipeline failed: ${res.statusText}`);
        }

        return await res.json();
    },
});






// ─── Task 11: NHL ML Training Reminder ──────────────────────
export const nhlMlReminder = task({
    id: "nhl-ml-reminder",

    retry: standardRetry,
    run: async () => {
        // Automatically checkpoint and wait for 14 days
        await wait.for({ days: 14 });

        const res = await fetch(`${API_URL}/api/trigger/nhl-ml-reminder`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${CRON_SECRET}`
            },
        });

        if (!res.ok) {
            throw new Error(`NHL ML reminder failed: ${res.statusText}`);
        }

        return await res.json();
    },
});

// ─── Task 11: NHL Fetch Odds (CRON 22:00 UTC = 23h Paris) ─────
export const nhlFetchOdds = schedules.task({
    id: "nhl-fetch-odds",

    retry: standardRetry,
    cron: "0 22 * * *",
    run: async () => {
        const res = await fetch(`${API_URL}/api/trigger/nhl-fetch-odds`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${CRON_SECRET}`
            },
        });

        if (!res.ok) {
            throw new Error(`NHL fetch odds failed: ${res.statusText}`);
        }

        return await res.json();
    },
});




