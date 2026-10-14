import { deprecate } from "./deprecate.js";

const DEFAULTS = Object.freeze({ token: undefined, timeoutMs: 5000, retries: 0, headers: {} });
const KNOWN = new Set(["baseUrl", "token", "timeoutMs", "retries", "headers"]);

function normalize(input) {
  for (const key of Object.keys(input)) {
    if (!KNOWN.has(key)) throw new TypeError(`unknown client option "${key}"`);
  }
  const merged = { ...DEFAULTS };
  for (const [key, value] of Object.entries(input)) {
    if (value !== undefined) merged[key] = value;
  }
  const { baseUrl, token, timeoutMs, retries, headers } = merged;
  if (typeof baseUrl !== "string" || baseUrl === "") {
    throw new TypeError("baseUrl must be a non-empty string");
  }
  if (typeof timeoutMs !== "number" || !Number.isFinite(timeoutMs) || timeoutMs <= 0) {
    throw new RangeError("timeoutMs must be a positive number");
  }
  if (!Number.isInteger(retries) || retries < 0) {
    throw new RangeError("retries must be a non-negative integer");
  }
  return Object.freeze({
    baseUrl: baseUrl.replace(/\/+$/, ""),
    token,
    timeoutMs,
    retries,
    headers: Object.freeze({ ...headers }),
  });
}

/**
 * Create an API client.
 *
 * createClient({ baseUrl, token, timeoutMs = 5000, retries = 0, headers = {} })
 *
 * The old positional form createClient(baseUrl, token, timeoutMs, retries) still
 * works but is deprecated (code CLIENT_POSITIONAL_ARGS).
 */
export function createClient(baseUrlOrOptions, token, timeoutMs, retries) {
  let input;
  if (typeof baseUrlOrOptions === "string") {
    deprecate(
      "CLIENT_POSITIONAL_ARGS",
      "createClient(baseUrl, token, timeoutMs, retries) is deprecated; pass an options object instead",
    );
    input = { baseUrl: baseUrlOrOptions, token, timeoutMs, retries };
  } else if (baseUrlOrOptions !== null && typeof baseUrlOrOptions === "object" && !Array.isArray(baseUrlOrOptions)) {
    input = baseUrlOrOptions;
  } else {
    throw new TypeError("createClient expects an options object");
  }
  const options = normalize(input);

  return {
    options,
    /**
     * Describe a request and pass it to `transport`, returning whatever the transport returns.
     */
    request(transport, method, path, body) {
      const headers = { accept: "application/json", ...options.headers };
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
