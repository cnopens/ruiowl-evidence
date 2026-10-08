import { describe, expect, it } from "vitest";
import { calculateInvoice, validateInvoiceRequest } from "../src/invoice";

describe("calculateInvoice", () => {
  it("charges tax on a plain single-line invoice with no discount", () => {
    const result = calculateInvoice({
      lines: [{ sku: "A1", unitPrice: 100, quantity: 1 }],
      taxRate: 0.13,
      discountRate: 0,
    });
    expect(result.subtotal).toBe(100);
    expect(result.discount).toBe(0);
    expect(result.tax).toBeCloseTo(13, 5);
    expect(result.total).toBeCloseTo(113, 5);
  });

  it("applies a small discount before tax (discountRate <= 0.3)", () => {
    const result = calculateInvoice({
      lines: [
        { sku: "A1", unitPrice: 120, quantity: 1 },
        { sku: "B2", unitPrice: 80, quantity: 1 },
      ],
      taxRate: 0.13,
      discountRate: 0.1,
    });
    expect(result.subtotal).toBe(200);
    expect(result.discount).toBeCloseTo(20, 5);
    // Tax base is the discounted amount: 200 − 20 = 180.
    expect(result.tax).toBeCloseTo(23.4, 5);
    expect(result.total).toBeCloseTo(203.4, 5);
  });

  it("still taxes the discounted amount for high-volume discounts (> 0.3)", () => {
    const result = calculateInvoice({
      lines: [{ sku: "C3", unitPrice: 500, quantity: 1 }],
      taxRate: 0.13,
      discountRate: 0.4,
    });
    expect(result.subtotal).toBe(500);
    expect(result.discount).toBeCloseTo(200, 5);
    // Tax base must be subtotal − discount = 300, never the full subtotal.
    expect(result.tax).toBeCloseTo(39, 5);
    expect(result.total).toBeCloseTo(339, 5);
  });
});

describe("validateInvoiceRequest", () => {
  it("accepts a well-formed request", () => {
    const req = validateInvoiceRequest({
      lines: [{ sku: "A1", unitPrice: 10, quantity: 2 }],
      taxRate: 0.05,
    });
    expect(req.lines).toHaveLength(1);
    expect(req.discountRate).toBe(0);
  });

  it("rejects a negative quantity", () => {
    expect(() =>
      validateInvoiceRequest({
        lines: [{ sku: "A1", unitPrice: 10, quantity: -1 }],
        taxRate: 0.05,
      }),
    ).toThrow(/quantity/);
  });

  it("rejects unit prices with more than 2 decimal places", () => {
    // Money is whole cents; sub-cent prices must be rejected (README "Pricing").
    expect(() =>
      validateInvoiceRequest({
        lines: [{ sku: "A1", unitPrice: 10.005, quantity: 1 }],
        taxRate: 0.05,
      }),
    ).toThrow(/decimal/i);
    expect(() =>
      validateInvoiceRequest({
        lines: [{ sku: "A1", unitPrice: 10.001, quantity: 1 }],
        taxRate: 0.05,
      }),
    ).toThrow(/decimal/i);
  });
});
