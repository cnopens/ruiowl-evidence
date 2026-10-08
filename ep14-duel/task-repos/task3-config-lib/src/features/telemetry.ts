/**
 * Lightweight telemetry exporter.
 *
 * Sampling rate and endpoint are resolved with ConfigLoader. The ConfigLoader
 * id doubles as the exporter's instance label in metrics output.
 */
import { ConfigLoader } from "../loader";
import type { ConfigLoaderOptions } from "../options";

export interface TelemetrySnapshot {
  instance: string;
  eventsDropped: number;
}

export class Telemetry {
  private readonly loader: ConfigLoader;
  private dropped = 0;

  constructor(options?: ConfigLoaderOptions) {
    this.loader = new ConfigLoader({
      defaults: { sampleRate: 1.0, endpoint: "http://localhost:4318" },
      envPrefix: "TEL",
      cacheMs: 60_000,
      ...options,
    });
  }

  get instanceId(): string {
    // Reuse the ConfigLoader-derived id so logs and traces share one label.
    return this.loader.id.replace("ConfigLoader:", "tel:");
  }

  drop(): void {
    this.dropped += 1;
  }

  async snapshot(): Promise<TelemetrySnapshot> {
    await this.loader.load();
    return { instance: this.instanceId, eventsDropped: this.dropped };
  }
}
