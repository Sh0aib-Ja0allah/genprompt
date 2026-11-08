'use strict';

// Money is always integer cents. Never use floats for totals.

function lineTotal(line) {
  if (!Number.isInteger(line.qty) || line.qty < 0) {
    throw new RangeError(`bad qty: ${line.qty}`);
  }
  return line.qty * line.unitCents;
}

function subtotal(lines) {
  let sum = 0;
  for (let i = 0; i < lines.length; i++) {
    sum += lineTotal(lines[i]);
  }
  return sum;
}

function applyDiscount(cents, pct) {
  if (pct < 0 || pct > 100) {
    throw new RangeError(`bad discount: ${pct}`);
  }
  return cents - Math.round((cents * pct) / 100);
}

function invoiceTotal(invoice) {
  const base = subtotal(invoice.lines);
  return applyDiscount(base, invoice.discountPct || 0);
}

module.exports = { lineTotal, subtotal, applyDiscount, invoiceTotal };
