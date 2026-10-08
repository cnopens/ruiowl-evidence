/** Error type thrown by the config library. */
export declare class ConfigError extends Error {
    readonly code: string;
    readonly cause?: unknown;
    constructor(code: string, message: string, cause?: unknown);
}
