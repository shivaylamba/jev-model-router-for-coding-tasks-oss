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
   * Send `message` to one recipient. The recipient is trimmed before sending.
   * Throws TypeError if the recipient is empty or only whitespace.
   */
  notify(recipient: string, message: string): void {
    const to = recipient.trim();
    if (to === "") {
      throw new TypeError("recipient must be a non-empty string");
    }
    this.transport.send(to, message);
  }
}
