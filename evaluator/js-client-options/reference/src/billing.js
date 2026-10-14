import { createClient } from "./client.js";

// Billing calls are slow and idempotent, so allow a longer timeout and retry.
export function createBillingApi(config) {
  const client = createClient({ baseUrl: config.billingUrl, token: config.token, timeoutMs: 15000, retries: 3 });
  return {
    client,
    charge: (transport, customerId, cents) =>
      client.request(transport, "POST", "/charges", { customerId, cents }),
  };
}
