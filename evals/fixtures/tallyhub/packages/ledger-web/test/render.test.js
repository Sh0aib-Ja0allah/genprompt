'use strict';
const test = require('node:test');
const assert = require('node:assert');
const { renderTable } = require('../src/render');

test('renderTable adds a total row', () => {
  const html = renderTable([{ label: 'A', cents: 100 }, { label: 'B', cents: 50 }]);
  assert.match(html, /<th>Total<\/th><th>150<\/th>/);
});
