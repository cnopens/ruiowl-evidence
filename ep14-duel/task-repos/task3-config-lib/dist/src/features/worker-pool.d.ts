import type { ConfigSourceOptions } from "../options";
export declare class WorkerPool {
    private readonly loader;
    constructor(options?: ConfigSourceOptions);
    get label(): string;
    size(): Promise<number>;
}
