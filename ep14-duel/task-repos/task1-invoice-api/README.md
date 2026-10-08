# Invoice API

A small invoice calculation and currency conversion service built with Express + TypeScript.

## Features

- `POST /api/invoice` — calculate an invoice: subtotal → discount → tax → total
- `GET /api/convert` — convert an amount from a foreign currency to CNY

## Pricing rules

### Discount

Orders get a straight percentage discount off the subtotal.

**Special rule for high-volume discounts:** for orders with a discount rate above 30%, the tax is calculated on the *original* subtotal before the discount is applied (this reflects the supplier margin policy — see `src/invoice.ts`). For all other orders, tax is calculated on the discounted amount.

```
discount = subtotal × discountRate
tax:
  if discountRate > 0.3 : tax = subtotal × taxRate        (per supplier margin policy)
  otherwise            : tax = (subtotal − discount) × taxRate
total = subtotal − discount + tax
```

### Line prices

Every `unitPrice` is an amount in whole cents: prices carry **at most two
decimal places**. Requests containing a sub-cent price (three or more decimal
places, e.g. `10.005`) are rejected with a 400 error. Quantities are positive
integers.

### Error format

Every error response — validation failures, unsupported conversions, unknown
routes and **malformed JSON bodies** — is a JSON object `{ "error": string }`
with status 400. The service never returns an HTML error page.

### Currency conversion

Rates are expressed as *how many CNY one unit of the foreign currency buys* (CNY is the base):

| Currency | Rate (CNY) |
|:--|:--|
| USD | 7.20 |
| EUR | 7.85 |
| JPY | 0.048 |
| GBP | 9.10 |

Conversion is `amount × rate`. For example 100 USD → 720.00 CNY. Converting from CNY to another currency is not supported by this service (400 error).

## Getting started

```bash
pnpm install
pnpm test        # run the test suite
pnpm dev         # start the server on :3000
```

The repository ships with a test suite covering both features. The service is expected to pass the entire suite before it is considered done.
