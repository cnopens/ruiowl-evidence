import type { ConfigSourceOptions } from "../options";
/** A single scheduled job definition. */
export type JobSpec = {
    name: string;
    cron: string;
};
export declare class Scheduler {
    private readonly loader;
    private jobs;
    constructor(options?: ConfigSourceOptions);
    /** Reload job specs from the ConfigSource sources. */
    refresh(): Promise<void>;
    list(): JobSpec[];
}
/** Convenience wrapper around {@link Scheduler} that shares loader state. */
export declare function buildScheduler(options?: ConfigSourceOptions): Promise<Scheduler>;
