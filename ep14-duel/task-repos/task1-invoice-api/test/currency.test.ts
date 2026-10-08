import { describe, expect, it } from "vitest";
import { convertToCny } from "../src/currency";

describe("convertToCny", () => {
  it("converts EUR to CNY with the listed rate", () => {
    // 100 EUR × 7.85 = 785.00 CNY
    expect(convertToCny(100, "EUR")).toBeCloseTo(785, 5);
  });

  it("converts USD to CNY with the listed rate", () => {
    // 100 USD × 7.20 = 720.00 CNY
    expect(convertToCny(100, "USD")).toBeCloseTo(720, 5);
  });

  it("rejects unknown currencies and non-positive amounts", () => {
    expect(() => convertToCny(100, "XXX")).toThrow(/unsupported currency/);
    expect(() => convertToCny(0, "USD")).toThrow(/positive/);
    expect(() => convertToCny(100, "CNY")).toThrow(/not supported/);
  });
});
