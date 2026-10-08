# config-lib API notes

## ConfigLoader

`ConfigLoader` is the class-based entry point. Construct it with
`ConfigLoaderOptions`:

```ts
const loader = new ConfigLoader({
  file: "./app.json",
  envPrefix: "APP",
  cacheMs: 0,
});
await loader.load(); // merged ConfigObject
loader.invalidate();
```

### ConfigLoaderOptions

| Field | Type | Default | Meaning |
|:--|:--|:--|:--|
| `file` | `string` | — | JSON/YAML file path (middle layer) |
| `envPrefix` | `string` | `APP` | env layer prefix |
| `defaults` | `ConfigObject` | — | lowest-precedence layer |
| `cacheMs` | `number` | `0` | cache merged result (ms) |
| `required` | `string[]` | `[]` | keys that must resolve |

## loadWithLoader / loadConfig

- `loadWithLoader(options)` — functional wrapper constructing a `ConfigLoader`
  internally.
- `loadConfig(options)` — identical convenience alias exported from the index.

Both return `Promise<ConfigObject>`. Type-level validation is available via
`loadValidated(options, schema)` from the schema module.

## id format

`ConfigLoader` instances expose `id`:

```
ConfigLoader:<file-or-(defaults+env)>:<envPrefix>
```

The exact string is part of the observable behaviour of the library and is
asserted by the test suite (`test/loader.test.ts`).
