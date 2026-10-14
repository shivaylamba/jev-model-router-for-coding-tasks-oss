/**
 * Create an API client.
 *
 * @param {string} baseUrl   e.g. "https://api.internal.example"; a trailing slash is ignored
 * @param {string} [token]   bearer token; no Authorization header when omitted
 * @param {number} [timeoutMs=5000]
 * @param {number} [retries=0]
 */
export function createClient(baseUrl, token, timeoutMs = 5000, retries = 0) {
  if (typeof baseUrl !== "string" || baseUrl === "") {
    throw new TypeError("baseUrl must be a non-empty string");
  }
  const options = Object.freeze({
    baseUrl: baseUrl.replace(/\/+$/, ""),
    token,
    timeoutMs,
    retries,
  });

  return {
    options,
    /**
     * Describe a request and pass it to `transport`, returning whatever the transport returns.
     */
    request(transport, method, path, body) {
      const headers = { accept: "application/json" };
      if (options.token) headers.authorization = `Bearer ${options.token}`;
      if (body !== undefined) headers["content-type"] = "application/json";
      return transport({
        method,
        url: options.baseUrl + (path.startsWith("/") ? path : `/${path}`),
        headers,
        body: body === undefined ? undefined : JSON.stringify(body),
        timeoutMs: options.timeoutMs,
        retries: options.retries,
      });
    },
  };
}
