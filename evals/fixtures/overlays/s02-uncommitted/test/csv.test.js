'use strict';
const test = require('node:test');
const assert = require('node:assert');
const { quote, toCsvRows } = require('../src/csv');

test('quote leaves plain fields alone', () => {
  assert.strictEqual(quote('Widget'), 'Widget');
});

test('quote wraps commas and doubles quotes', () => {
  assert.strictEqual(quote('Gadget, "large"'), '"Gadget, ""large"""');
});

test('toCsvRows writes a header, one row per line and a TOTAL row', () => {
  const out = toCsvRows({ lines: [{ label: 'A', qty: 2, unitCents: 100 }] });
  assert.strictEqual(out, 'label,qty,unitCents,lineCents\nA,2,100,200\nTOTAL,,,0\n');
});
