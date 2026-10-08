import type { ConfigObject } from "../types";
/** Wrap a defaults object as the lowest-precedence config layer. */
export declare function defaultsLayer(defaults: ConfigObject | undefined): ConfigObject;
