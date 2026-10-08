import type { ConfigSourceOptions } from "../options";
export interface TelemetrySnapshot {
    instance: string;
    eventsDropped: number;
}
export declare class Telemetry {
    private readonly loader;
    private dropped;
    constructor(options?: ConfigSourceOptions);
    get instanceId(): string;
    drop(): void;
    snapshot(): Promise<TelemetrySnapshot>;
}
