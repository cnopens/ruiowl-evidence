"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Telemetry = void 0;
/**
 * Lightweight telemetry exporter.
 *
 * Sampling rate and endpoint are resolved with ConfigSource. The ConfigSource
 * id doubles as the exporter's instance label in metrics output.
 */
const loader_1 = require("../loader");
class Telemetry {
    loader;
    dropped = 0;
    constructor(options) {
        this.loader = new loader_1.ConfigSource({
            defaults: { sampleRate: 1.0, endpoint: "http://localhost:4318" },
            envPrefix: "TEL",
            cacheMs: 60_000,
            ...options,
        });
    }
    get instanceId() {
        // Reuse the ConfigSource-derived id so logs and traces share one label.
        return this.loader.id.replace("ConfigSource:", "tel:");
    }
    drop() {
        this.dropped += 1;
    }
    async snapshot() {
        await this.loader.load();
        return { instance: this.instanceId, eventsDropped: this.dropped };
    }
}
exports.Telemetry = Telemetry;
