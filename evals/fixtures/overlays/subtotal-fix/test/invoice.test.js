'use strict';
const test = require('node:test');
const assert = require('node:assert');
const { lineTotal, applyDiscount, invoiceTotal } = require('../src/invoice');

test('lineTotal multiplies qty by unit cents', () => {
  assert.strictEqual(lineTotal({ qty: 3, unitCents: 250 }), 750);
});

test('lineTotal rejects a negative qty', () => {
  assert.throws(() => lineTotal({ qty: -1, unitCents: 100 }), RangeError);
});

test('applyDiscount rounds to the nearest cent', () => {
  assert.strictEqual(applyDiscount(999, 10), 899);
});

test('invoiceTotal of an empty invoice is zero', () => {
  assert.strictEqual(invoiceTotal({ lines: [] }), 0);
});

test('invoiceTotal counts every line, including the first', () => {
  const invoice = {
    discountPct: 10,
    lines: [
      { qty: 2, unitCents: 1250 },
      { qty: 1, unitCents: 4000 },
      { qty: 1, unitCents: 500 },
    ],
  };
  assert.strictEqual(invoiceTotal(invoice), 6300);
});
