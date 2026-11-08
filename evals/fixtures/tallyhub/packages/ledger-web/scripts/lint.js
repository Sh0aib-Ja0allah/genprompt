'use strict';
// Minimal lint for this package: no trailing whitespace, no tabs, no console.log in src/.
const fs = require('fs');
const path = require('path');

let problems = 0;
for (const root of ['src', 'test', 'scripts']) {
  for (const name of fs.readdirSync(root)) {
    if (!name.endsWith('.js')) continue;
    const file = path.join(root, name);
    fs.readFileSync(file, 'utf8').split('\n').forEach((line, i) => {
      const where = `${file}:${i + 1}`;
      if (/[ \t]+$/.test(line)) { console.error(`${where} trailing whitespace`); problems++; }
      if (/\t/.test(line)) { console.error(`${where} tab`); problems++; }
      if (root === 'src' && /console\.log/.test(line)) { console.error(`${where} console.log`); problems++; }
    });
  }
}
if (problems) { console.error(`${problems} problem(s)`); process.exit(1); }
console.log('ledger-web lint: 0 problems');
