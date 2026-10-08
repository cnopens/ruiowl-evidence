"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.loadFileLayer = loadFileLayer;
const fs_1 = require("fs");
const errors_1 = require("../errors");
const registry_1 = require("../format/registry");
/** Load and parse a JSON or YAML config file into an object. */
async function loadFileLayer(filePath) {
    const ext = filePath.split(".").pop()?.toLowerCase() ?? "";
    const parse = (0, registry_1.getParser)(ext);
    if (!parse) {
        throw new errors_1.ConfigError("UNSUPPORTED_FILE_TYPE", `unsupported config file extension: .${ext}`);
    }
    let text;
    try {
        text = await fs_1.promises.readFile(filePath, "utf8");
    }
    catch (err) {
        throw new errors_1.ConfigError("FILE_READ_FAILED", `cannot read config file ${filePath}`, err);
    }
    const parsed = parse(text, filePath);
    if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
        throw new errors_1.ConfigError("FILE_NOT_OBJECT", `config file must contain a JSON object: ${filePath}`);
    }
    return parsed;
}
