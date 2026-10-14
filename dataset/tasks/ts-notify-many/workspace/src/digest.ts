import type { Notifier } from "./notifier.ts";

export function sendDigest(notifier: Notifier, subscribers: string[], items: string[]): void {
  const body = items.length === 0 ? "Nothing new today." : items.map((item) => `- ${item}`).join("\n");
  for (const subscriber of subscribers) {
    notifier.notify(subscriber, body);
  }
}
