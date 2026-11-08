'use strict';

function addCents(...values) {
  return values.reduce((sum, v) => {
    if (!Number.isInteger(v)) throw new TypeError(`not integer cents: ${v}`);
    return sum + v;
  }, 0);
}

// Splits total into `parts` integer amounts that add up to total exactly.
// Largest-remainder: the first (total % parts) shares get one extra cent.
function splitCents(total, parts) {
  if (!Number.isInteger(total) || !Number.isInteger(parts) || parts < 1) {
    throw new RangeError(`bad split: ${total} / ${parts}`);
  }
  const base = Math.floor(total / parts);
  const extra = total - base * parts;
  return Array.from({ length: parts }, (_, i) => base + (i < extra ? 1 : 0));
}

module.exports = { addCents, splitCents };
