// scratch: poking at csv output by hand. Not part of the slice.
const { toCsvRows } = require('./src/csv');
process.stdout.write(toCsvRows(require('./examples/sample.json')));
