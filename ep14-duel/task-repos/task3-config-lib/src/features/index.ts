/**
 * Feature-module aggregator.
 *
 * Re-exports the sample features that consume ConfigLoader. Keeping them in
 * one barrel makes the "config-lib powers the whole app" story easy to follow.
 */
export { startServer } from "./server";
export type { ServerHandle } from "./server";
export { Scheduler, buildScheduler } from "./scheduler";
export type { JobSpec } from "./scheduler";
export { Telemetry } from "./telemetry";
export type { TelemetrySnapshot } from "./telemetry";
export { FeatureFlags, KNOWN_FLAGS } from "./feature-flag";
export { WorkerPool } from "./worker-pool";
export { createApiClient } from "./api-client";
export type { ApiClientConfig } from "./api-client";
export { warmCache, WARMER_INSTANCES } from "./cache-warm";
