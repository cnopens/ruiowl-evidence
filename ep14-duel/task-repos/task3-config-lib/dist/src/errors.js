"use strict";
/** Error type thrown by the config library. */
Object.defineProperty(exports, "__esModule", { value: true });
exports.ConfigError = void 0;
class ConfigError extends Error {
    code;
    cause;
    constructor(code, message, cause) {
        super(message);
        this.name = "ConfigError";
        this.code = code;
        this.cause = cause;
    }
}
exports.ConfigError = ConfigError;
