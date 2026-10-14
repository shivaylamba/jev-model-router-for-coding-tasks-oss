import { test } from "node:test";
import assert from "node:assert/strict";
import { validateSignup } from "../src/signup.ts";

const TODAY = new Date(Date.UTC(2024, 5, 15, 12, 0, 0)); // 2024-06-15

function valid(overrides: Record<string, unknown> = {}) {
  return {
    username: "alice_01",
    email: "alice@example.com",
    password: "s3cretpass",
    confirmPassword: "s3cretpass",
    birthDate: "1990-04-01",
    ...overrides,
  };
}

function errorsOf(input: Record<string, unknown>, today: Date = TODAY) {
  const result = validateSignup(input, today);
  return result.ok ? {} : result.errors;
}

test("valid input is normalized", () => {
  const result = validateSignup(
    valid({ username: "  Alice_01 ", email: " Alice@Example.COM ", birthDate: " 1990-04-01 " }),
    TODAY,
  );
  assert.deepEqual(result, {
    ok: true,
    value: { username: "alice_01", email: "alice@example.com", birthDate: "1990-04-01" },
  });
});

test("everything missing", () => {
  assert.deepEqual(validateSignup({}, TODAY), {
    ok: false,
    errors: {
      username: "required",
      email: "required",
      password: "required",
      confirmPassword: "required",
      birthDate: "required",
    },
  });
});

test("non-strings and blanks are required", () => {
  assert.deepEqual(errorsOf(valid({ username: 42, email: "   ", birthDate: null })), {
    username: "required",
    email: "required",
    birthDate: "required",
  });
});

test("only invalid fields are reported", () => {
  assert.deepEqual(errorsOf(valid({ email: "nope" })), { email: "format" });
});

test("username rules in order", () => {
  assert.equal(errorsOf(valid({ username: "ab" })).username, "length");
  assert.equal(errorsOf(valid({ username: "a".repeat(21) })).username, "length");
  assert.equal(errorsOf(valid({ username: "a".repeat(20) })).username, undefined);
  assert.equal(errorsOf(valid({ username: "  ab  " })).username, "length");
  assert.equal(errorsOf(valid({ username: "a!" })).username, "length");
  assert.equal(errorsOf(valid({ username: "1abc" })).username, "format");
  assert.equal(errorsOf(valid({ username: "ab-cd" })).username, "format");
  assert.equal(errorsOf(valid({ username: "_abc" })).username, "format");
});

test("email format", () => {
  for (const email of ["a@b", "a@@b.com", "@b.com", "a@.b.com", "a@b.com.", "a b@c.com", "a@b..com", "ab.com"]) {
    assert.equal(errorsOf(valid({ email })).email, "format", email);
  }
  assert.equal(errorsOf(valid({ email: "first.last@mail.example.co" })).email, undefined);
});

test("password rules in order", () => {
  assert.equal(errorsOf(valid({ password: "short1", confirmPassword: "short1" })).password, "length");
  const long = "a1".repeat(32) + "b";
  assert.equal(errorsOf(valid({ password: long, confirmPassword: long })).password, "length");
  const max = "a1".repeat(32);
  assert.equal(errorsOf(valid({ password: max, confirmPassword: max })).password, undefined);
  assert.equal(errorsOf(valid({ password: "longpassword", confirmPassword: "longpassword" })).password, "weak");
  assert.equal(errorsOf(valid({ password: "12345678", confirmPassword: "12345678" })).password, "weak");
  assert.equal(errorsOf(valid({ password: "x9ALICE_01x", confirmPassword: "x9ALICE_01x" })).password, "contains_username");
});

test("password is not trimmed", () => {
  assert.equal(errorsOf(valid({ password: " pass1 ", confirmPassword: " pass1 " })).password, "length");
  assert.equal(errorsOf(valid({ password: " s3cretpass", confirmPassword: "s3cretpass" })).confirmPassword, "mismatch");
});

test("contains_username only applies to a valid username", () => {
  assert.deepEqual(errorsOf(valid({ username: "a1", password: "xa1xxxxx", confirmPassword: "xa1xxxxx" })), {
    username: "length",
  });
});

test("confirmPassword", () => {
  assert.equal(errorsOf(valid({ confirmPassword: "different1" })).confirmPassword, "mismatch");
  assert.equal(errorsOf(valid({ confirmPassword: undefined })).confirmPassword, "required");
  assert.deepEqual(errorsOf(valid({ password: undefined, confirmPassword: "whatever1" })), { password: "required" });
  assert.deepEqual(errorsOf(valid({ password: "short1", confirmPassword: "short2" })), {
    password: "length",
    confirmPassword: "mismatch",
  });
});

test("birthDate format", () => {
  for (const birthDate of ["2000-02-30", "1999-2-03", "1999-02-3", "99-02-03", "1899-12-31", "2001-02-29", "2000-13-01", "2000/01/01", "2000-01-01T00:00"]) {
    assert.equal(errorsOf(valid({ birthDate })).birthDate, "format", birthDate);
  }
  assert.equal(errorsOf(valid({ birthDate: "2000-02-29" })).birthDate, undefined);
  assert.equal(errorsOf(valid({ birthDate: "1900-01-01" })).birthDate, undefined);
});

test("birthDate in the future", () => {
  assert.equal(errorsOf(valid({ birthDate: "2024-06-16" })).birthDate, "future");
  assert.equal(errorsOf(valid({ birthDate: "2024-06-15" })).birthDate, "too_young");
});

test("thirteenth birthday", () => {
  assert.equal(errorsOf(valid({ birthDate: "2011-06-15" })).birthDate, undefined);
  assert.equal(errorsOf(valid({ birthDate: "2011-06-16" })).birthDate, "too_young");
  assert.equal(errorsOf(valid({ birthDate: "2011-07-01" })).birthDate, "too_young");
  assert.equal(errorsOf(valid({ birthDate: "2010-12-31" })).birthDate, undefined);
});

test("February 29 birthdays", () => {
  const feb28 = new Date(Date.UTC(2021, 1, 28));
  const mar1 = new Date(Date.UTC(2021, 2, 1));
  assert.equal(errorsOf(valid({ birthDate: "2008-02-29" }), feb28).birthDate, "too_young");
  assert.equal(errorsOf(valid({ birthDate: "2008-02-29" }), mar1).birthDate, undefined);
  const leapFeb29 = new Date(Date.UTC(2024, 1, 29));
  assert.equal(errorsOf(valid({ birthDate: "2011-02-28" }), leapFeb29).birthDate, undefined);
});

test("only the UTC date of today matters", () => {
  // 2024-06-14T23:30 UTC is still the 14th.
  const lateEvening = new Date(Date.UTC(2024, 5, 14, 23, 30));
  assert.equal(errorsOf(valid({ birthDate: "2011-06-15" }), lateEvening).birthDate, "too_young");
  assert.equal(errorsOf(valid({ birthDate: "2024-06-15" }), lateEvening).birthDate, "future");
});
