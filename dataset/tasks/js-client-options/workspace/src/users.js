import { createClient } from "./client.js";

export function createUsersApi(config) {
  const client = createClient(config.apiUrl, config.token);
  return {
    client,
    getUser: (transport, id) => client.request(transport, "GET", `/users/${encodeURIComponent(id)}`),
  };
}
