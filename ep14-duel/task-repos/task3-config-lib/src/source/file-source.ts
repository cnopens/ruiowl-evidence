import { promises as fs } from "fs";
import { ConfigError } from "../errors";
import { getParser } from "../format/registry";
import type { ConfigObject } from "../types";

/** Load and parse a JSON or YAML config file into an object. */
export async function loadFileLayer(filePath: string): Promise<ConfigObject> {
  const ext = filePath.split(".").pop()?.toLowerCase() ?? "";
  const parse = getParser(ext);
  if (!parse) {
    throw new ConfigError("UNSUPPORTED_FILE_TYPE", `unsupported config file extension: .${ext}`);
  }
  let text: string;
  try {
    text = await fs.readFile(filePath, "utf8");
  } catch (err) {
    throw new ConfigError("FILE_READ_FAILED", `cannot read config file ${filePath}`, err);
  }
  const parsed = parse(text, filePath);
  if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
    throw new ConfigError("FILE_NOT_OBJECT", `config file must contain a JSON object: ${filePath}`);
  }
  return parsed as ConfigObject;
}
