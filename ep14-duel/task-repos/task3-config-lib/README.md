# config-lib

A small typed configuration library with **layered sources** and optional
caching. The library resolves configuration from three sources, in increasing
order of precedence:

1. **defaults** — a plain object you pass in
2. **file** — an optional JSON or YAML file
3. **environment** — variables prefixed with `envPrefix` (default `APP`)

## Quick start

```ts
import { ConfigLoader, loadConfig } from "config-lib";

// Functional entry point
const cfg = await loadConfig({
  defaults: { port: 3000, log: { level: "info" } },
  file: "./app.json",
  envPrefix: "APP",
});

// Class-based entry point (same options)
const loader = new ConfigLoader({ defaults: { port: 3000 } });
const config = await loader.load();
console.log(loader.id); // "ConfigLoader:(defaults+env):APP"
```

## Options

`ConfigLoaderOptions`:

| Option | Type | Default | Meaning |
|:--|:--|:--|:--|
| `file` | `string` | — | path to a JSON/YAML config file |
| `envPrefix` | `string` | `APP` | env vars `APP_X` map to key `x`; `APP_A__B` maps to nested `a.b` |
| `defaults` | `object` | — | lowest-precedence layer |
| `cacheMs` | `number` | `0` | cache merged result for N ms (`0` = off) |
| `required` | `string[]` | `[]` | dotted keys that must exist after merging |

## Validation

`schema.ts` exposes `SchemaEntry` and `validateSchema` for runtime type
checks, and `loadValidated(options, schema)` combines load + validate.

## Development

```bash
pnpm install
pnpm build    # tsc → dist/
pnpm test     # vitest
```

The package is compiled with `strict` mode; the public surface is re-exported
from `src/index.ts` (`ConfigLoader`, `loadConfig`, `ConfigLoaderOptions`,
`SchemaEntry`, …).
