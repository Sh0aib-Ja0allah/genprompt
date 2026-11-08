'use strict';

const { lineTotal, invoiceTotal } = require('./invoice');

function quote(field) {
  const s = String(field);
  if (/[",\n]/.test(s)) {
    return `"${s.replace(/"/g, '""')}"`;
  }
  return s;
}

function toCsvRows(invoice) {
  const rows = [['label', 'qty', 'unitCents', 'lineCents']];
  for (const line of invoice.lines) {
    rows.push([line.label || '', line.qty, line.unitCents, lineTotal(line)]);
  }
  rows.push(['TOTAL', '', '', invoiceTotal(invoice)]);
  return rows.map((r) => r.map(quote).join(',')).join('\n') + '\n';
}

module.exports = { quote, toCsvRows };
