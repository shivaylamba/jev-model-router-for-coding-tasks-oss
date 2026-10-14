import { createClient } from "./client.js";

// Reports are public and generated on demand: no token, long timeout.
export function createReportsApi(config) {
  const client = createClient(config.reportsUrl, undefined, 60000);
  return {
    client,
    monthly: (transport, month) => client.request(transport, "GET", `/reports/${month}`),
  };
}
