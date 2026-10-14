import { test, beforeEach } from "node:test";
import assert from "node:assert/strict";
import { createClient } from "../src/client.js";
import { createUsersApi } from "../src/users.js";
import { createBillingApi } from "../src/billing.js";
import { createReportsApi } from "../src/reports.js";
import { resetDeprecations, setDeprecationHandler } from "../src/deprecate.js";

const echo = (req) => req;
let warnings = [];

beforeEach(() => {
  warnings = [];
  resetDeprecations();
  setDeprecationHandler((code, message) => warnings.push({ code, message }));
});

test("options object with defaults", () => {
  const client = createClient({ baseUrl: "https://api.example/" });
  assert.equal(client.options.baseUrl, "https://api.example");
  assert.equal(client.options.token, undefined);
  assert.equal(client.options.timeoutMs, 5000);
  assert.equal(client.options.retries, 0);
  assert.deepEqual(client.options.headers, {});
  assert.deepEqual(warnings, []);
});

test("options object with every option", () => {
  const client = createClient({ baseUrl: "https://api.example", token: "t", timeoutMs: 250, retries: 2, headers: { "x-team": "core" } });
  const req = client.request(echo, "GET", "/ping");
  assert.equal(req.url, "https://api.example/ping");
  assert.equal(req.headers.authorization, "Bearer t");
  assert.equal(req.headers["x-team"], "core");
  assert.equal(req.headers.accept, "application/json");
  assert.equal(req.timeoutMs, 250);
  assert.equal(req.retries, 2);
});

test("undefined option values fall back to defaults", () => {
  const client = createClient({ baseUrl: "https://api.example", timeoutMs: undefined, retries: undefined });
  assert.equal(client.options.timeoutMs, 5000);
  assert.equal(client.options.retries, 0);
});

test("validation", () => {
  assert.throws(() => createClient({}), TypeError);
  assert.throws(() => createClient({ baseUrl: "" }), TypeError);
  assert.throws(() => createClient({ baseUrl: "https://a", timeoutMs: 0 }), RangeError);
  assert.throws(() => createClient({ baseUrl: "https://a", timeoutMs: -5 }), RangeError);
  assert.throws(() => createClient({ baseUrl: "https://a", retries: -1 }), RangeError);
  assert.throws(() => createClient({ baseUrl: "https://a", retries: 1.5 }), RangeError);
  assert.throws(() => createClient(), TypeError);
});

test("unknown option names are rejected, naming the option", () => {
  assert.throws(() => createClient({ baseUrl: "https://a", timeout: 100 }), (err) => err instanceof TypeError && err.message.includes("timeout"));
});

test("positional form still works and warns once", () => {
  const client = createClient("https://api.example/", "t0k", 1000, 1);
  assert.equal(client.options.baseUrl, "https://api.example");
  assert.equal(client.options.token, "t0k");
  assert.equal(client.options.timeoutMs, 1000);
  assert.equal(client.options.retries, 1);
  createClient("https://other.example");
  createClient("https://third.example", "x");
  assert.equal(warnings.length, 1);
  assert.equal(warnings[0].code, "CLIENT_POSITIONAL_ARGS");
});

test("positional form uses the same defaults and validation", () => {
  const client = createClient("https://api.example");
  assert.equal(client.options.timeoutMs, 5000);
  assert.equal(client.options.retries, 0);
  assert.throws(() => createClient("https://api.example", "t", 0), RangeError);
});

test("options form never warns", () => {
  createClient({ baseUrl: "https://a" });
  createClient({ baseUrl: "https://b", token: "x" });
  assert.equal(warnings.length, 0);
});

test("callers use the options form and keep their settings", () => {
  const config = { apiUrl: "https://u.example", billingUrl: "https://b.example", reportsUrl: "https://r.example", token: "s3cret" };
  const users = createUsersApi(config).getUser(echo, "42");
  const charge = createBillingApi(config).charge(echo, "c1", 500);
  const report = createReportsApi(config).monthly(echo, "2026-01");
  assert.deepEqual(warnings, []);
  assert.equal(users.url, "https://u.example/users/42");
  assert.equal(users.headers.authorization, "Bearer s3cret");
  assert.equal(users.timeoutMs, 5000);
  assert.equal(charge.timeoutMs, 15000);
  assert.equal(charge.retries, 3);
  assert.equal(charge.body, '{"customerId":"c1","cents":500}');
  assert.equal(report.timeoutMs, 60000);
  assert.equal(report.retries, 0);
  assert.equal(report.headers.authorization, undefined);
});
