"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Scheduler = void 0;
exports.buildScheduler = buildScheduler;
/**
 * Scheduler that drives periodic jobs.
 *
 * Job cadence and enabled flags come from a ConfigSource-backed configuration,
 * so operators can change schedules without redeploying.
 */
const loader_1 = require("../loader");
const DEFAULT_JOBS = [
    { name: "heartbeat", cron: "*/5 * * * *" },
];
class Scheduler {
    loader;
    jobs = DEFAULT_JOBS;
    constructor(options) {
        // Scheduler keeps its own ConfigSource instance; the id includes the env
        // prefix so multiple environments can run side by side.
        this.loader = new loader_1.ConfigSource({
            defaults: { jobs: DEFAULT_JOBS },
            envPrefix: "SCHED",
            cacheMs: 30_000,
            ...options,
        });
    }
    /** Reload job specs from the ConfigSource sources. */
    async refresh() {
        const cfg = await this.loader.load();
        this.jobs = cfg.jobs ?? DEFAULT_JOBS;
        this.loader.invalidate(); // force re-read next refresh
    }
    list() {
        return this.jobs;
    }
}
exports.Scheduler = Scheduler;
/** Convenience wrapper around {@link Scheduler} that shares loader state. */
async function buildScheduler(options) {
    const sched = new Scheduler(options);
    await sched.refresh();
    return sched;
}
