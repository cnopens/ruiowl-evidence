/** Expand a leading "~/" into the user home directory. */
export function expandHome(filePath: string): string {
  if (filePath === "~") return process.env.HOME ?? filePath;
  if (filePath.startsWith("~/")) {
    const home = process.env.HOME ?? "";
    return home ? filePath.replace(/^~\//, `${home}/`) : filePath;
  }
  return filePath;
}
