import { debounce } from "./debounce.js";

/**
 * Connect a search input to a search function. `search(query)` is called at
 * most once per pause in typing, with the latest query, and at least every
 * second while the user keeps typing.
 */
export function createSearchBox(search, { scheduler } = {}) {
  const run = debounce((query) => search(query.trim()), 250, { maxWait: 1000, scheduler });
  return {
    input(text) {
      run(text);
    },
    submit() {
      run.flush();
    },
    clear() {
      run.cancel();
    },
  };
}
