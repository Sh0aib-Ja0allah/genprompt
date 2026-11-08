'use strict';
// Writes dist/index.html from a sample table (the web team's build step).
const fs = require('fs');
const { renderTable } = require('../src/render');

fs.mkdirSync('dist', { recursive: true });
fs.writeFileSync('dist/index.html', renderTable([{ label: 'Sample', cents: 1234 }]));
console.log('ledger-web build: dist/index.html');
