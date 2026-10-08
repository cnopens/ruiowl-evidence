import type { ConfigSource } from "../loader";
/** Emit a one-line debug message tagged with the loader's identity. */
export declare function logLoad(loader: ConfigSource, layerCount: number, tookMs: number): void;
