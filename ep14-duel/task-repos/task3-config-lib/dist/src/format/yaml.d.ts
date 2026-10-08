/**
 * Minimal YAML-subset parser used by the config library.
 *
 * Supports flat `key: value` mappings and block nesting by indentation.
 * It is intentionally small — the library targets simple config files, not
 * the full YAML spec.
 */
export declare function parseYaml(text: string): unknown;
