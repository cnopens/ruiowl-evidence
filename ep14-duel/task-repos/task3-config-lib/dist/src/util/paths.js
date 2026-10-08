"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.expandHome = expandHome;
/** Expand a leading "~/" into the user home directory. */
function expandHome(filePath) {
    if (filePath === "~")
        return process.env.HOME ?? filePath;
    if (filePath.startsWith("~/")) {
        const home = process.env.HOME ?? "";
        return home ? filePath.replace(/^~\//, `${home}/`) : filePath;
    }
    return filePath;
}
