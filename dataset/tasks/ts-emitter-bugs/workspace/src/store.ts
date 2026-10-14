import { Emitter } from "./emitter.ts";

export type ChangeListener = (key: string, value: unknown, previous: unknown) => void;

/** A key-value store that notifies subscribers of every change. */
export class Store {
  private values = new Map<string, unknown>();
  private events = new Emitter();

  get(key: string): unknown {
    return this.values.get(key);
  }

  set(key: string, value: unknown): void {
    const previous = this.values.get(key);
    if (Object.is(previous, value)) return;
    this.values.set(key, value);
    this.events.emit("change", key, value, previous);
  }

  /** Call `listener` on every change. Returns an unsubscribe function. */
  subscribe(listener: ChangeListener): () => void {
    return this.events.on("change", listener as (...args: unknown[]) => void);
  }

  /** Call `listener` on the next change only. Returns a function that cancels it. */
  subscribeOnce(listener: ChangeListener): () => void {
    return this.events.once("change", listener as (...args: unknown[]) => void);
  }
}
