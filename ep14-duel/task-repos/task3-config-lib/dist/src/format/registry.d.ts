type Parser = (text: string, fileName: string) => unknown;
/** Look up the parser registered for a file extension. */
export declare function getParser(ext: string): Parser | undefined;
/** Register a custom parser for a file extension. */
export declare function registerParser(ext: string, parser: Parser): void;
export {};
