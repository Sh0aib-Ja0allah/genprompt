'use strict';
const test = require('node:test');
const assert = require('node:assert');
const { addCents, splitCents } = require('../src/money');

test('addCents sums integer cents', () => {
  assert.strictEqual(addCents(100, 250, 5), 355);
});

test('addCents rejects floats', () => {
  assert.throws(() => addCents(1.5), TypeError);
});

test('splitCents keeps the sum exact', () => {
  assert.deepStrictEqual(splitCents(1000, 3), [334, 333, 333]);
});
