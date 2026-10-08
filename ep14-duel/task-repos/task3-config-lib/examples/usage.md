# Example: wiring config-lib into an application

All sample snippets below assume the classic usage: a `ConfigLoader` instance
built once at boot, then shared.

## Server + scheduler

```ts
import { ConfigLoader } from "config-lib";
import { startServer } from "./features/server";
import { buildScheduler } from "./features/scheduler";

// One ConfigLoader for the whole process…
const loader = new ConfigLoader({ file: "./app.json", envPrefix: "APP" });
const cfg = await loader.load();

// …and feature modules that each own their own ConfigLoader:
await startServer({ file: "./server.json" });
await buildScheduler({ defaults: { jobs: [] } });
```

## Feature flags

```ts
import { ConfigLoader, type ConfigLoaderOptions } from "config-lib";

// ConfigLoaderOptions can be spread into the loader constructor:
const opts: ConfigLoaderOptions = { envPrefix: "APP", cacheMs: 5_000 };
const loader = new ConfigLoader(opts);
```

## API client

```ts
import { loadWithLoader } from "config-lib";
const client = await loadWithLoader({ envPrefix: "API" });
```

Notes:

- The `ConfigLoader.id` getter returns a stable label like
  `ConfigLoader:(defaults+env):APP` — useful in logs and traces.
- `ConfigLoaderOptions.defaults` is merged first; environment wins.
- See `docs/api.md` for the full option table.
