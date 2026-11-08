'use strict';

const { addCents } = require('../../ledger-core/src/money');

function renderTable(lines) {
  const rows = lines.map((l) => `<tr><td>${l.label}</td><td>${l.cents}</td></tr>`).join('');
  const total = addCents(...lines.map((l) => l.cents));
  return `<table>${rows}<tr><th>Total</th><th>${total}</th></tr></table>`;
}

module.exports = { renderTable };
