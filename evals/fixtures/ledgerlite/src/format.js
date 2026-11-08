'use strict';

function formatCents(cents, currency = 'EUR') {
  const sign = cents < 0 ? '-' : '';
  const abs = Math.abs(cents);
  const whole = Math.floor(abs / 100);
  const frac = String(abs % 100).padStart(2, '0');
  return `${sign}${whole}.${frac} ${currency}`;
}

module.exports = { formatCents };
