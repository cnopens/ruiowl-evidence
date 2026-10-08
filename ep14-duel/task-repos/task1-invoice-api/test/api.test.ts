import { afterAll, describe, expect, it } from "vitest";
import type { AddressInfo } from "node:net";
import { app } from "../src/index";

/**
 * Route-level (HTTP) contract tests.
 *
 * The README promises that every error response is JSON of the shape
 * { "error": string } — including malformed request bodies, which
 * express.json() rejects before any route handler runs.
 */

const server = app.listen(0);
afterAll(() => {
  server.close();
});

function baseUrl(): string {
  const { port } = server.address() as AddressInfo;
  return `http://127.0.0.1:${port}`;
}

describe("POST /api/invoice error contract", () => {
  it("answers malformed JSON with a JSON error body, not an HTML page", async () => {
    const res = await fetch(`${baseUrl()}/api/invoice`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: '{"lines": [{"sku": "A1", "unitPrice": ',
    });
    expect(res.status).toBe(400);
    expect(res.headers.get("content-type")).toMatch(/application\/json/);
    const body = (await res.json()) as { error?: string };
    expect(typeof body.error).toBe("string");
    expect(body.error!.length).toBeGreaterThan(0);
  });

  it("answers a validation failure with a JSON error body", async () => {
    const res = await fetch(`${baseUrl()}/api/invoice`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ lines: [], taxRate: 0.13 }),
    });
    expect(res.status).toBe(400);
    const body = (await res.json()) as { error?: string };
    expect(typeof body.error).toBe("string");
  });
});
