/** Primitive config value types. */
export type ConfigScalar = string | number | boolean | null;
export interface ConfigObject {
    [key: string]: ConfigScalar | ConfigObject | ConfigScalar[] | ConfigObject[];
}
export type ConfigValue = ConfigScalar | ConfigObject | ConfigScalar[] | ConfigObject[];
export type DeepPartial<T> = {
    [K in keyof T]?: T[K] extends object ? DeepPartial<T[K]> : T[K];
};
