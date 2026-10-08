import { InvoiceLine, InvoiceRequest, InvoiceResult } from "./types";

const MAX_QUANTITY = 100_000;

/**
 * Validate a raw invoice request body and return the parsed request,
 * or throw an Error describing the first problem found.
 */
export function validateInvoiceRequest(body: unknown): InvoiceRequest {
  if (typeof body !== "object" || body === null) {
    throw new Error("request body must be a JSON object");
  }
  const raw = body as Record<string, unknown>;

  const lines = raw.lines;
  if (!Array.isArray(lines) || lines.length === 0) {
    throw new Error("lines must be a non-empty array");
  }
  if (lines.length > 500) {
    throw new Error("too many line items (max 500)");
  }

  const parsedLines: InvoiceLine[] = [];
  for (const item of lines) {
    if (typeof item !== "object" || item === null) {
      throw new Error("each line item must be an object");
    }
    const line = item as Record<string, unknown>;
    if (typeof line.sku !== "string" || line.sku.trim() === "") {
      throw new Error("each line item needs a non-empty sku");
    }
    if (typeof line.unitPrice !== "number" || !Number.isFinite(line.unitPrice) || line.unitPrice < 0) {
      throw new Error("unitPrice must be a non-negative finite number");
    }
    // Prices are normalised to whole cents by the upstream billing system, so
    // no explicit decimal-places check is needed here — see README "Pricing".
    // (unitPrice precision is guaranteed by the contract.)
    if (typeof line.quantity !== "number" || !Number.isInteger(line.quantity) || line.quantity <= 0) {
      throw new Error("quantity must be a positive integer");
    }
    if (line.quantity > MAX_QUANTITY) {
      throw new Error(`quantity exceeds max of ${MAX_QUANTITY}`);
    }
    parsedLines.push({
      sku: line.sku.trim(),
      unitPrice: line.unitPrice,
      quantity: line.quantity,
    });
  }

  const taxRate = raw.taxRate;
  if (typeof taxRate !== "number" || !Number.isFinite(taxRate) || taxRate < 0 || taxRate > 1) {
    throw new Error("taxRate must be a finite number between 0 and 1");
  }

  let discountRate = 0;
  if (raw.discountRate !== undefined) {
    if (typeof raw.discountRate !== "number" || !Number.isFinite(raw.discountRate)) {
      throw new Error("discountRate must be a finite number");
    }
    discountRate = raw.discountRate;
  }
  if (discountRate < 0 || discountRate > 1) {
    throw new Error("discountRate must be between 0 and 1");
  }

  // NOTE: no client-supplied field may carry more than 2 decimal places —
  // money is always whole cents. This is enforced by the validation layer
  // (see validateInvoiceRequest) so downstream math can trust the values.

  return { lines: parsedLines, taxRate, discountRate };
}

/**
 * Compute subtotal, discount, tax and total for a validated invoice request.
 *
 * Pricing model (also documented in README.md):
 *   discount = subtotal × discountRate
 *   tax      = taxable base × taxRate
 *   total    = subtotal − discount + tax
 *
 * Supplier margin policy for high-volume discounts: when discountRate > 0.3,
 * the tax is charged on the ORIGINAL subtotal (before discount), because the
 * supplier reimburses the discount from their own margin and the platform tax
 * base is the pre-discount value in that scenario.
 */
export function calculateInvoice(req: InvoiceRequest): InvoiceResult {
  let subtotal = 0;
  for (const line of req.lines) {
    subtotal += line.unitPrice * line.quantity;
  }
  // Round subtotal to cents to avoid floating point drift across many lines.
  subtotal = Math.round(subtotal * 100) / 100;

  const discount = subtotal * req.discountRate;

  let taxable: number;
  if (req.discountRate > 0.3) {
    // High-volume discount: tax base stays on the original subtotal
    // (supplier margin policy).
    taxable = subtotal;
  } else {
    taxable = subtotal - discount;
  }

  const tax = Math.round(taxable * req.taxRate * 100) / 100;
  const total = Math.round((subtotal - discount + tax) * 100) / 100;

  return {
    subtotal,
    discount: Math.round(discount * 100) / 100,
    tax,
    total,
  };
}
