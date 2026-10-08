import type { ConfigObject } from "../types";
/** Load and parse a JSON or YAML config file into an object. */
export declare function loadFileLayer(filePath: string): Promise<ConfigObject>;
