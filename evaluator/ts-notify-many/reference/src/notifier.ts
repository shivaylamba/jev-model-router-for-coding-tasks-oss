export interface Transport {
  send(recipient: string, message: string): void;
}

/** Records every send in memory. Handy in tests and dry runs. */
export class MemoryTransport implements Transport {
  sent: Array<{ recipient: string; message: string }> = [];

  send(recipient: string, message: string): void {
    this.sent.push({ recipient, message });
  }
}

export class Notifier {
  private transport: Transport;

  constructor(transport: Transport) {
    this.transport = transport;
  }

  /**
   * Send `message` to one recipient or a list of recipients and return how
   * many messages were sent. Recipients are trimmed; duplicates (compared
   * case-insensitively after trimming) are sent once, using the first spelling.
   * Throws TypeError, before sending anything, if any recipient is blank.
   */
  notify(recipients: string | readonly string[], message: string): number {
    const list = typeof recipients === "string" ? [recipients] : recipients;
    const unique = new Map<string, string>();
    for (const recipient of list) {
      const to = recipient.trim();
      if (to === "") {
        throw new TypeError("recipient must be a non-empty string");
      }
      const seen = to.toLowerCase();
      if (!unique.has(seen)) unique.set(seen, to);
    }
    for (const to of unique.values()) {
      this.transport.send(to, message);
    }
    return unique.size;
  }
}
