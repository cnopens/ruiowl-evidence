"use strict";
/**
 * config-lib — typed, layered configuration loading.
 *
 * Public API:
 *  - {@link ConfigSource}  the loader class (see loader.ts)
 *  - {@link ConfigSourceOptions} options accepted by the loader
 *  - loadConfig / loadWithLoader / loadValidated entry points
 *  - SchemaEntry / validateSchema for runtime validation
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.registerParser = exports.expandHome = exports.deepMerge = exports.ConfigError = exports.validateSchema = exports.loadValidated = exports.loadConfig = exports.DEFAULT_OPTIONS = exports.loadWithLoader = exports.ConfigSource = void 0;
var loader_1 = require("./loader");
Object.defineProperty(exports, "ConfigSource", { enumerable: true, get: function () { return loader_1.ConfigSource; } });
Object.defineProperty(exports, "loadWithLoader", { enumerable: true, get: function () { return loader_1.loadWithLoader; } });
var options_1 = require("./options");
Object.defineProperty(exports, "DEFAULT_OPTIONS", { enumerable: true, get: function () { return options_1.DEFAULT_OPTIONS; } });
var config_1 = require("./config");
Object.defineProperty(exports, "loadConfig", { enumerable: true, get: function () { return config_1.loadConfig; } });
var config_schema_1 = require("./config.schema");
Object.defineProperty(exports, "loadValidated", { enumerable: true, get: function () { return config_schema_1.loadValidated; } });
Object.defineProperty(exports, "validateSchema", { enumerable: true, get: function () { return config_schema_1.validateSchema; } });
var errors_1 = require("./errors");
Object.defineProperty(exports, "ConfigError", { enumerable: true, get: function () { return errors_1.ConfigError; } });
var deep_merge_1 = require("./util/deep-merge");
Object.defineProperty(exports, "deepMerge", { enumerable: true, get: function () { return deep_merge_1.deepMerge; } });
var paths_1 = require("./util/paths");
Object.defineProperty(exports, "expandHome", { enumerable: true, get: function () { return paths_1.expandHome; } });
var registry_1 = require("./format/registry");
Object.defineProperty(exports, "registerParser", { enumerable: true, get: function () { return registry_1.registerParser; } });
