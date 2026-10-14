import { test } from "node:test";
import assert from "node:assert/strict";
import { createClient } from "../src/client.js";
import { createUsersApi } from "../src/users.js";
import { createBillingApi } from "../src/billing.js";
import { createReportsApi } from "../src/reports.js";
import { resetDeprecations, setDeprecationHandler } from "../src/deprecate.js";

const echo = (req) => req;
setDeprecationHandler(() => {});

test("request description", () => {
  resetDeprecations();
  const client = createClient("https://api.example/", "t0k", 1000, 1);
  assert.deepEqual(client.request(echo, "POST", "items", { a: 1 }), {
    method: "POST",
    url: "https://api.example/items",
    headers: { accept: "application/json", authorization: "Bearer t0k", "content-type": "application/json" },
    body: '{"a":1}',
    timeoutMs: 1000,
    retries: 1,
  });
});

test("defaults", () => {
  const client = createClient("https://api.example");
  assert.equal(client.options.timeoutMs, 5000);
  assert.equal(client.options.retries, 0);
  assert.equal(client.request(echo, "GET", "/x").headers.authorization, undefined);
});

test("services", () => {
  const config = { apiUrl: "https://u.example", billingUrl: "https://b.example", reportsUrl: "https://r.example", token: "s3cret" };
  assert.equal(createUsersApi(config).getUser(echo, "a b").url, "https://u.example/users/a%20b");
  const charge = createBillingApi(config).charge(echo, "c1", 500);
  assert.equal(charge.timeoutMs, 15000);
  assert.equal(charge.retries, 3);
  const report = createReportsApi(config).monthly(echo, "2026-01");
  assert.equal(report.timeoutMs, 60000);
  assert.equal(report.headers.authorization, undefined);
});
