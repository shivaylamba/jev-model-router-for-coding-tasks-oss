import type { Notifier } from "./notifier.ts";

export interface Alert {
  service: string;
  level: "warning" | "critical";
  text: string;
}

/** Page the on-call engineer for critical alerts only. */
export function dispatchAlert(notifier: Notifier, onCall: string, alert: Alert): boolean {
  if (alert.level !== "critical") return false;
  notifier.notify(onCall, `[${alert.service}] ${alert.text}`);
  return true;
}
