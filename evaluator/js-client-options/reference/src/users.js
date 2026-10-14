import { createClient } from "./client.js";

export function createUsersApi(config) {
  const client = createClient({ baseUrl: config.apiUrl, token: config.token });
  return {
    client,
    getUser: (transport, id) => client.request(transport, "GET", `/users/${encodeURIComponent(id)}`),
  };
}
