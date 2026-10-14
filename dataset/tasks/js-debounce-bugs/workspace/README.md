# searchbox

The search-as-you-type widget logic: `src/debounce.js` limits how often the
search request fires, `src/searchbox.js` wires it to the input.

Timers go through an injectable scheduler (`{ now, setTimeout, clearTimeout }`)
so tests can drive time by hand; see `test/fake-scheduler.js`.

Plain JavaScript ES modules on Node 24, no dependencies. Run the tests with
`node --test`.
