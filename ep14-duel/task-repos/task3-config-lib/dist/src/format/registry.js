"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.getParser = getParser;
exports.registerParser = registerParser;
const errors_1 = require("../errors");
const json_1 = require("./json");
const yaml_1 = require("./yaml");
const REGISTRY = {
    json: (text) => (0, json_1.parseJson)(text),
    yaml: (text) => (0, yaml_1.parseYaml)(text),
    yml: (text) => (0, yaml_1.parseYaml)(text),
};
/** Look up the parser registered for a file extension. */
function getParser(ext) {
    return REGISTRY[ext];
}
/** Register a custom parser for a file extension. */
function registerParser(ext, parser) {
    if (!/^[a-z0-9]{1,8}$/.test(ext)) {
        throw new errors_1.ConfigError("INVALID_EXTENSION", `bad extension: ${ext}`);
    }
    REGISTRY[ext] = parser;
}
