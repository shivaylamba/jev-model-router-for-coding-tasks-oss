/**
 * @typedef {object} Scheduler
 * @property {() => number} now
 * @property {(callback: () => void, ms: number) => unknown} setTimeout
 * @property {(id: unknown) => void} clearTimeout
 */

/** @type {Scheduler} */
const realScheduler = {
  now: () => Date.now(),
  setTimeout: (callback, ms) => setTimeout(callback, ms),
  clearTimeout: (id) => clearTimeout(id),
};

/**
 * Debounce `fn`.
 *
 * A burst is a run of calls each made less than `wait` ms after the previous
 * one; it ends `wait` ms after its last call.
 *
 * - leading (default false): the first call of a burst invokes `fn`
 *   immediately with that call's arguments.
 * - trailing (default true): when the burst ends, `fn` is invoked once with the
 *   arguments of the most recent call, unless every call of the burst has
 *   already been passed to `fn` (so a burst of one call with leading: true
 *   invokes `fn` once, not twice).
 * - maxWait (optional, ms): while a burst goes on, `fn` is also invoked with
 *   the most recent arguments once `maxWait` ms have passed since the first
 *   call whose arguments have not yet been passed to `fn`. This happens even
 *   when trailing is false. After it, the burst continues as before.
 * - scheduler: timer functions; defaults to the real clock and timers.
 *
 * `fn` is called with the `this` of the call whose arguments it receives.
 * Every call to the debounced function returns the result of the latest
 * invocation of `fn` so far (undefined before the first).
 *
 * The returned function has:
 * - cancel(): drops any invocation that has not happened yet and ends the
 *   burst; the next call starts a new burst.
 * - flush(): if there are arguments not yet passed to `fn`, invokes `fn` with
 *   the most recent ones now instead of later; either way it ends the burst
 *   and returns the result of the latest invocation.
 *
 * @template {(...args: any[]) => any} F
 * @param {F} fn
 * @param {number} wait
 * @param {{ leading?: boolean, trailing?: boolean, maxWait?: number, scheduler?: Scheduler }} [options]
 */
export function debounce(fn, wait, options = {}) {
  const { leading = false, trailing = true, maxWait, scheduler = realScheduler } = options;
  let waitTimer = null;
  let maxTimer = null;
  let pendingArgs = null;
  let pendingThis;
  let result;

  function invoke() {
    const args = pendingArgs;
    const thisArg = pendingThis;
    pendingArgs = null;
    pendingThis = undefined;
    result = fn.apply(thisArg, args);
    return result;
  }

  function onWait() {
    waitTimer = null;
    if (maxTimer !== null) {
      scheduler.clearTimeout(maxTimer);
      maxTimer = null;
    }
    if (trailing && pendingArgs !== null) invoke();
    pendingArgs = null;
  }

  function onMaxWait() {
    maxTimer = null;
    if (pendingArgs !== null) invoke();
  }

  function debounced(...args) {
    const startsBurst = waitTimer === null;
    if (waitTimer !== null) scheduler.clearTimeout(waitTimer);
    waitTimer = scheduler.setTimeout(onWait, wait);

    pendingArgs = args;
    pendingThis = this;
    if (startsBurst && leading) {
      return invoke();
    }
    if (maxWait !== undefined && maxTimer === null) {
      maxTimer = scheduler.setTimeout(onMaxWait, maxWait);
    }
    return result;
  }

  debounced.cancel = () => {
    if (waitTimer !== null) scheduler.clearTimeout(waitTimer);
    waitTimer = null;
    if (maxTimer !== null) scheduler.clearTimeout(maxTimer);
    maxTimer = null;
    pendingArgs = null;
    pendingThis = undefined;
  };

  debounced.flush = () => {
    if (waitTimer !== null) scheduler.clearTimeout(waitTimer);
    waitTimer = null;
    if (maxTimer !== null) {
      scheduler.clearTimeout(maxTimer);
      maxTimer = null;
    }
    if (pendingArgs !== null) invoke();
    return result;
  };

  return debounced;
}
