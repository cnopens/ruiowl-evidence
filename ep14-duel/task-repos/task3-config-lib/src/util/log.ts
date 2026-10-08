import type { ConfigLoader } from "../loader";

/** Emit a one-line debug message tagged with the loader's identity. */
export function logLoad(loader: ConfigLoader, layerCount: number, tookMs: number): void {
  const label = process.env.CONFIG_DEBUG === "1" ? console.debug : () => undefined;
  label(`[config] ${loader.id} merged ${layerCount} layer(s) in ${tookMs}ms`);
}
