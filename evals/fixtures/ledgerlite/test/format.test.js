'use strict';
const test = require('node:test');
const assert = require('node:assert');
const { formatCents } = require('../src/format');

test('formatCents pads the fraction', () => {
  assert.strictEqual(formatCents(1205), '12.05 EUR');
});

test('formatCents keeps the sign', () => {
  assert.strictEqual(formatCents(-50, 'USD'), '-0.50 USD');
});
