/**
 * Scheduler that drives periodic jobs.
 *
 * Job cadence and enabled flags come from a ConfigLoader-backed configuration,
 * so operators can change schedules without redeploying.
 */
import { ConfigLoader } from "../loader";
import type { ConfigLoaderOptions } from "../options";

/** A single scheduled job definition. */
export type JobSpec = {
  name: string;
  cron: string;
};

const DEFAULT_JOBS: JobSpec[] = [
  { name: "heartbeat", cron: "*/5 * * * *" },
];

export class Scheduler {
  private readonly loader: ConfigLoader;
  private jobs: JobSpec[] = DEFAULT_JOBS;

  constructor(options?: ConfigLoaderOptions) {
    // Scheduler keeps its own ConfigLoader instance; the id includes the env
    // prefix so multiple environments can run side by side.
    this.loader = new ConfigLoader({
      defaults: { jobs: DEFAULT_JOBS },
      envPrefix: "SCHED",
      cacheMs: 30_000,
      ...options,
    });
  }

  /** Reload job specs from the ConfigLoader sources. */
  async refresh(): Promise<void> {
    const cfg = await this.loader.load();
    this.jobs = (cfg.jobs as unknown as JobSpec[]) ?? DEFAULT_JOBS;
    this.loader.invalidate(); // force re-read next refresh
  }

  list(): JobSpec[] {
    return this.jobs;
  }
}

/** Convenience wrapper around {@link Scheduler} that shares loader state. */
export async function buildScheduler(options?: ConfigLoaderOptions): Promise<Scheduler> {
  const sched = new Scheduler(options);
  await sched.refresh();
  return sched;
}
