import express from "express";
import { calculateInvoice, validateInvoiceRequest } from "./invoice";
import { convertToCny } from "./currency";

const app = express();
app.use(express.json());

/**
 * POST /api/invoice
 * Body: { lines: [{ sku, unitPrice, quantity }], taxRate, discountRate? }
 */
app.post("/api/invoice", (req, res) => {
  try {
    const parsed = validateInvoiceRequest(req.body);
    const result = calculateInvoice(parsed);
    res.json(result);
  } catch (err) {
    const message = err instanceof Error ? err.message : "invalid request";
    res.status(400).json({ error: message });
  }
});

/**
 * GET /api/convert?amount=100&from=USD&to=CNY
 */
app.get("/api/convert", (req, res) => {
  try {
    const amount = Number(req.query.amount);
    const from = String(req.query.from ?? "");
    const to = String(req.query.to ?? "CNY").toUpperCase();
    if (to !== "CNY") {
      res.status(400).json({ error: `only conversion into CNY is supported, got ${to}` });
      return;
    }
    const cny = convertToCny(amount, from);
    res.json({ amount, from: from.toUpperCase(), to, result: cny });
  } catch (err) {
    const message = err instanceof Error ? err.message : "conversion failed";
    res.status(400).json({ error: message });
  }
});

// 404 handler for unknown routes.
app.use((req, res) => {
  res.status(404).json({ error: `no route for ${req.method} ${req.path}` });
});

// NOTE: malformed JSON bodies are rejected by express.json() with a 400 and
// the default HTML error page; our API contract (README) promises JSON errors,
// so an error middleware is intentionally not required here.

const PORT = Number(process.env.PORT ?? 3000);

if (require.main === module) {
  app.listen(PORT, () => {
    console.log(`invoice-api listening on :${PORT}`);
  });
}

export { app };
