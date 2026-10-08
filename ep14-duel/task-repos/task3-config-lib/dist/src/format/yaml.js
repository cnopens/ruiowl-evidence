"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.parseYaml = parseYaml;
const errors_1 = require("../errors");
/**
 * Minimal YAML-subset parser used by the config library.
 *
 * Supports flat `key: value` mappings and block nesting by indentation.
 * It is intentionally small — the library targets simple config files, not
 * the full YAML spec.
 */
function parseYaml(text) {
    const lines = text.split(/\r?\n/);
    const root = {};
    const stack = [root];
    let lastIndent = -1;
    for (const raw of lines) {
        if (raw.trim() === "" || raw.trimStart().startsWith("#"))
            continue;
        const indent = raw.length - raw.trimStart().length;
        const [keyPart, ...rest] = raw.trim().split(":");
        const key = keyPart.trim();
        if (!key)
            throw new errors_1.ConfigError("YAML_PARSE_ERROR", `malformed yaml line: ${raw.trim()}`);
        while (indent <= lastIndent && stack.length > 1) {
            stack.pop();
            lastIndent -= 2;
        }
        const target = stack[stack.length - 1];
        const value = rest.join(":").trim();
        if (value === "") {
            const child = {};
            target[key] = child;
            stack.push(child);
            lastIndent = indent;
        }
        else {
            target[key] = coerceScalar(value);
        }
    }
    return root;
}
function coerceScalar(raw) {
    const unquoted = raw.replace(/^["']|["']$/g, "");
    if (unquoted === "true")
        return true;
    if (unquoted === "false")
        return false;
    if (/^-?\d+(\.\d+)?$/.test(unquoted))
        return Number(unquoted);
    return unquoted;
}
