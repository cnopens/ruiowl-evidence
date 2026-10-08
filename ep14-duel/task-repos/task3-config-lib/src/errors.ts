/** Error type thrown by the config library. */

export class ConfigError extends Error {
  readonly code: string;
  readonly cause?: unknown;

  constructor(code: string, message: string, cause?: unknown) {
    super(message);
    this.name = "ConfigError";
    this.code = code;
    this.cause = cause;
  }
}
