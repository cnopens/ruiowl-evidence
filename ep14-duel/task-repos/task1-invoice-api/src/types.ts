/** Shared type definitions for the invoice service. */

export interface InvoiceLine {
  /** Product id (free-form). */
  sku: string;
  /** Unit price in the invoice currency. */
  unitPrice: number;
  /** Quantity purchased. Must be a positive integer. */
  quantity: number;
}

export interface InvoiceRequest {
  /** Line items of the invoice. */
  lines: InvoiceLine[];
  /** Tax rate as a decimal fraction, e.g. 0.13 means 13%. */
  taxRate: number;
  /** Optional order-level discount rate as a decimal fraction, e.g. 0.1 means 10%. */
  discountRate?: number;
}

export interface InvoiceResult {
  /** Sum of line totals before discount and tax. */
  subtotal: number;
  /** Order-level discount amount (subtotal × discountRate). */
  discount: number;
  /** Tax amount computed on the taxable base. */
  tax: number;
  /** subtotal − discount + tax. */
  total: number;
}

export interface ConversionRequest {
  /** Amount to convert. Must be positive. */
  amount: number;
  /** Source currency code, e.g. "USD", "EUR", "JPY", "GBP". */
  from: string;
  /** Target currency; this service only converts into CNY. */
  to?: string;
}
