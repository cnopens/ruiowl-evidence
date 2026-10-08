"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.validateSchema = validateSchema;
exports.loadValidated = loadValidated;
const loader_1 = require("./loader");
/** Validate a loaded config against a schema. */
function validateSchema(config, schema) {
    for (const entry of schema) {
        const parts = entry.key.split(".");
        let cursor = config;
        let missing = false;
        for (const part of parts) {
            if (typeof cursor !== "object" || cursor === null || !(part in cursor)) {
                missing = true;
                break;
            }
            cursor = cursor[part];
        }
        if (missing) {
            if (entry.required) {
                throw new Error(`config key ${entry.key} is required but missing`);
            }
            continue;
        }
        const actual = typeof cursor;
        if (entry.type === "object") {
            if (typeof cursor !== "object" || cursor === null || Array.isArray(cursor)) {
                throw new Error(`config key ${entry.key} must be an object, got ${actual}`);
            }
        }
        else if (actual !== entry.type) {
            throw new Error(`config key ${entry.key} must be ${entry.type}, got ${actual}`);
        }
    }
}
/**
 * Load config and validate it against a schema in one step.
 * The loader instance is created internally, so schema-aware callers get a
 * single entry point instead of juggling a {@link ConfigSource} themselves.
 */
async function loadValidated(options, schema, LoaderCtor = loader_1.ConfigSource) {
    const loader = new LoaderCtor(options);
    const config = await loader.load();
    validateSchema(config, schema);
    return config;
}
