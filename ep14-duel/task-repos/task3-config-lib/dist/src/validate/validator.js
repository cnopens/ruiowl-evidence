"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.validateRequired = validateRequired;
const errors_1 = require("../errors");
/** Fail when any of `requiredKeys` is missing from the merged config. */
function validateRequired(config, requiredKeys) {
    for (const dotted of requiredKeys) {
        const parts = dotted.split(".");
        let cursor = config;
        for (const part of parts) {
            if (typeof cursor !== "object" || cursor === null || !(part in cursor)) {
                throw new errors_1.ConfigError("MISSING_REQUIRED_KEY", `missing required config key: ${dotted}`);
            }
            cursor = cursor[part];
        }
    }
}
