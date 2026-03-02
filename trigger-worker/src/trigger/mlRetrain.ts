import { schedules } from "@trigger.dev/sdk/v3";

export const mlRetrainTask = schedules.task({
    id: "ml-retrain-weekly",
    cron: "0 5 * * 6", // Run every Saturday at 05:00 AM UTC (before WE games)
    run: async (payload) => {
        console.log(`[MLOps] Starting weekly continuous training round at ${payload.timestamp}`);

        const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://api.probalab.fr";
        const CRON_SECRET = process.env.CRON_SECRET;

        if (!CRON_SECRET) {
            throw new Error("Missing CRON_SECRET environment variable");
        }

        try {
            const response = await fetch(`${API_URL}/api/trigger/retrain-models`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${CRON_SECRET}`,
                },
            });

            if (!response.ok) {
                const text = await response.text();
                throw new Error(`API returned ${response.status}: ${text}`);
            }

            const data = await response.json();
            console.log("[MLOps] Success:", data);

            return {
                success: true,
                trainedAt: new Date().toISOString(),
                apiResponse: data,
            };
        } catch (error) {
            console.error("[MLOps] Failed to run retrain-models:", error);
            throw error;
        }
    },
});
