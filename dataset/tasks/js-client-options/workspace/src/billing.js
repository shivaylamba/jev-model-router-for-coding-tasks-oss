import { createClient } from "./client.js";

// Billing calls are slow and idempotent, so allow a longer timeout and retry.
export function createBillingApi(config) {
  const client = createClient(config.billingUrl, config.token, 15000, 3);
  return {
    client,
    charge: (transport, customerId, cents) =>
      client.request(transport, "POST", "/charges", { customerId, cents }),
  };
}
