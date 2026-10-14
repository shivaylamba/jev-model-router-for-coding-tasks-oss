export type Listener = (...args: unknown[]) => void;

/**
 * A minimal event emitter.
 *
 * Each call to `on` or `once` creates one registration, so the same function
 * registered twice is called twice per emit.
 */
export class Emitter {
  private listeners = new Map<string, Listener[]>();

  /** Register `listener` for `event`. Returns a function that removes this registration. */
  on(event: string, listener: Listener): () => void {
    const list = this.listeners.get(event) ?? [];
    list.push(listener);
    this.listeners.set(event, list);
    return () => this.off(event, listener);
  }

  /**
   * Register `listener` to be called on the next emit of `event` only. The
   * registration is removed just before the listener is called. Until then it
   * counts in `listenerCount` and can be removed with `off(event, listener)` or
   * with the returned function.
   */
  once(event: string, listener: Listener): () => void {
    const wrapper: Listener = (...args) => {
      this.off(event, wrapper);
      listener(...args);
    };
    return this.on(event, wrapper);
  }

  /**
   * Remove the earliest registration of `listener` for `event`, whether it was
   * added with `on` or `once`. Does nothing if it is not registered.
   */
  off(event: string, listener: Listener): void {
    const list = this.listeners.get(event);
    if (!list) return;
    const index = list.indexOf(listener);
    if (index !== -1) list.splice(index, 1);
  }

  /**
   * Call the listeners registered for `event`, in registration order, with
   * `args`. Returns true if `event` had at least one listener when emit started.
   *
   * The listeners called by one emit are fixed when it starts: listeners
   * registered while the emit is running are first called by the next emit,
   * and a listener removed while the emit is running is not called by it if
   * its turn has not come yet. Removing a listener never causes another
   * listener to be skipped.
   */
  emit(event: string, ...args: unknown[]): boolean {
    const list = this.listeners.get(event);
    if (!list || list.length === 0) return false;
    for (let i = 0; i < list.length; i++) {
      list[i](...args);
    }
    return true;
  }

  /** Number of registrations for `event`. */
  listenerCount(event: string): number {
    return this.listeners.get(event)?.length ?? 0;
  }
}
