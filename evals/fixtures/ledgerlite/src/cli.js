#!/usr/bin/env node
'use strict';

// CLI entry. Grew by accretion: parsing, validation, maths and printing all live here.
const fs = require('fs');
const { invoiceTotal, lineTotal } = require('./invoice');
const { formatCents } = require('./format');

function main(argv) {
  var file = argv[2];
  if (!file) { process.stderr.write('usage: ledgerlite <invoice.json> [--currency XXX] [--lines]\n'); return 2; }
  var currency = 'EUR';
  var showLines = false;
  for (var i = 3; i < argv.length; i++) {
    if (argv[i] === '--currency') { currency = argv[i + 1]; i++; }
    else if (argv[i] === '--lines') { showLines = true; }
    else { process.stderr.write('unknown flag ' + argv[i] + '\n'); return 2; }
  }
  var raw;
  try { raw = fs.readFileSync(file, 'utf8'); } catch (e) { process.stderr.write('cannot read ' + file + '\n'); return 1; }
  var invoice;
  try { invoice = JSON.parse(raw); } catch (e) { process.stderr.write('bad json\n'); return 1; }
  if (!invoice || !Array.isArray(invoice.lines)) { process.stderr.write('invoice.lines missing\n'); return 1; }
  if (showLines) {
    invoice.lines.forEach(function (l) {
      process.stdout.write((l.label || '?') + '  ' + formatCents(lineTotal(l), currency) + '\n');
    });
  }
  process.stdout.write('TOTAL  ' + formatCents(invoiceTotal(invoice), currency) + '\n');
  return 0;
}

if (require.main === module) {
  process.exitCode = main(process.argv);
}

module.exports = { main };
