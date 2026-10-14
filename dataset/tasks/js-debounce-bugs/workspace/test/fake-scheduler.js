/** A manual clock with timers, for tests. Timers due at the same time run in creation order. */
export function createFakeScheduler() {
  let now = 0;
  let nextId = 1;
  const timers = new Map();
  return {
    now: () => now,
    setTimeout(callback, ms) {
      const id = nextId++;
      timers.set(id, { at: now + ms, callback });
      return id;
    },
    clearTimeout(id) {
      timers.delete(id);
    },
    /** Move time forward by `ms`, running every timer that becomes due. */
    advance(ms) {
      const target = now + ms;
      for (;;) {
        let dueId = null;
        let due = null;
        for (const [id, timer] of timers) {
          if (timer.at <= target && (due === null || timer.at < due.at)) {
            dueId = id;
            due = timer;
          }
        }
        if (due === null) break;
        timers.delete(dueId);
        now = due.at;
        due.callback();
      }
      now = target;
    },
    pending: () => timers.size,
  };
}
