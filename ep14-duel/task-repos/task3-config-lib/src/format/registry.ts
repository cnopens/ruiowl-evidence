import { ConfigError } from "../errors";
import { parseJson } from "./json";
import { parseYaml } from "./yaml";

type Parser = (text: string, fileName: string) => unknown;

const REGISTRY: Record<string, Parser> = {
  json: (text) => parseJson(text),
  yaml: (text) => parseYaml(text),
  yml: (text) => parseYaml(text),
};

/** Look up the parser registered for a file extension. */
export function getParser(ext: string): Parser | undefined {
  return REGISTRY[ext];
}

/** Register a custom parser for a file extension. */
export function registerParser(ext: string, parser: Parser): void {
  if (!/^[a-z0-9]{1,8}$/.test(ext)) {
    throw new ConfigError("INVALID_EXTENSION", `bad extension: ${ext}`);
  }
  REGISTRY[ext] = parser;
}
