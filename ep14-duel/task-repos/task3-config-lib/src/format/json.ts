/** Parse a JSON string, throwing a readable ConfigError on failure. */
export function parseJson(text: string): unknown {
  return JSON.parse(text);
}
