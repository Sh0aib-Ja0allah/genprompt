'use strict';
const test = require('node:test');
const assert = require('node:assert');
const { quote, toCsvRows } = require('../src/csv');
const { main } = require('../src/cli');

test('quote leaves plain fields alone', () => {
  assert.strictEqual(quote('Widget'), 'Widget');
});

test('quote wraps commas and doubles quotes', () => {
  assert.strictEqual(quote('Gadget, "large"'), '"Gadget, ""large"""');
});

test('toCsvRows writes a header, one row per line and a TOTAL row', () => {
  const out = toCsvRows({ lines: [{ label: 'A', qty: 2, unitCents: 100 }] });
  assert.strictEqual(out, 'label,qty,unitCents,lineCents\nA,2,100,200\nTOTAL,,,200\n');
});

test('cli --csv prints the CSV and exits 0', () => {
  const chunks = [];
  const write = process.stdout.write;
  process.stdout.write = (s) => { chunks.push(String(s)); return true; };
  let code;
  try {
    code = main(['node', 'cli', 'examples/sample.json', '--csv']);
  } finally {
    process.stdout.write = write;
  }
  assert.strictEqual(code, 0);
  assert.match(chunks.join(''), /^label,qty,unitCents,lineCents\n/);
  assert.match(chunks.join(''), /\nTOTAL,,,6300\n$/);
});
