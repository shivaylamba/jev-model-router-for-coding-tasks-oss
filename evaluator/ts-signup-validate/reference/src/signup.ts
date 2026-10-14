// Sign-up validation. Rules: docs/signup-rules.md
import { daysInMonth, isLeapYear } from "./dates.ts";
import type { SignupErrorCode, SignupErrors, SignupInput, SignupResult } from "./types.ts";

export type { SignupErrors, SignupInput, SignupResult } from "./types.ts";

function text(value: unknown, trim: boolean): string | null {
  if (typeof value !== "string") return null;
  const result = trim ? value.trim() : value;
  return result === "" ? null : result;
}

function checkUsername(username: string | null): SignupErrorCode | null {
  if (username === null) return "required";
  if (username.length < 3 || username.length > 20) return "length";
  if (!/^[A-Za-z][A-Za-z0-9_]*$/.test(username)) return "format";
  return null;
}

function checkEmail(email: string | null): SignupErrorCode | null {
  if (email === null) return "required";
  if (/\s/.test(email)) return "format";
  const parts = email.split("@");
  if (parts.length !== 2 || parts[0] === "") return "format";
  const labels = parts[1].split(".");
  if (labels.length < 2 || labels.some((label) => label === "")) return "format";
  return null;
}

function checkPassword(password: string | null, validUsername: string | null): SignupErrorCode | null {
  if (password === null) return "required";
  if (password.length < 8 || password.length > 64) return "length";
  if (!/[A-Za-z]/.test(password) || !/[0-9]/.test(password)) return "weak";
  if (validUsername !== null && password.toLowerCase().includes(validUsername.toLowerCase())) {
    return "contains_username";
  }
  return null;
}

interface Ymd {
  year: number;
  month: number;
  day: number;
}

function parseDate(value: string): Ymd | null {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!match) return null;
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  if (year < 1900 || month < 1 || month > 12 || day < 1 || day > daysInMonth(year, month)) return null;
  return { year, month, day };
}

function compare(a: Ymd, b: Ymd): number {
  return a.year - b.year || a.month - b.month || a.day - b.day;
}

function ageOn(birth: Ymd, today: Ymd): number {
  let age = today.year - birth.year;
  let anniversary = { year: today.year, month: birth.month, day: birth.day };
  if (birth.month === 2 && birth.day === 29 && !isLeapYear(today.year)) {
    anniversary = { year: today.year, month: 3, day: 1 };
  }
  if (compare(today, anniversary) < 0) age -= 1;
  return age;
}

function checkBirthDate(value: string | null, today: Ymd): SignupErrorCode | null {
  if (value === null) return "required";
  const birth = parseDate(value);
  if (birth === null) return "format";
  if (compare(birth, today) > 0) return "future";
  if (ageOn(birth, today) < 13) return "too_young";
  return null;
}

export function validateSignup(input: SignupInput, today: Date): SignupResult {
  const username = text(input.username, true);
  const email = text(input.email, true);
  const password = text(input.password, false);
  const confirm = text(input.confirmPassword, false);
  const birthDate = text(input.birthDate, true);
  const todayYmd = { year: today.getUTCFullYear(), month: today.getUTCMonth() + 1, day: today.getUTCDate() };

  const errors: SignupErrors = {};
  const usernameError = checkUsername(username);
  if (usernameError) errors.username = usernameError;
  const emailError = checkEmail(email);
  if (emailError) errors.email = emailError;
  const passwordError = checkPassword(password, usernameError ? null : username);
  if (passwordError) errors.password = passwordError;
  if (confirm === null) {
    errors.confirmPassword = "required";
  } else if (typeof input.password === "string" && confirm !== input.password) {
    errors.confirmPassword = "mismatch";
  }
  const birthError = checkBirthDate(birthDate, todayYmd);
  if (birthError) errors.birthDate = birthError;

  if (Object.keys(errors).length > 0) return { ok: false, errors };
  return {
    ok: true,
    value: { username: username!.toLowerCase(), email: email!.toLowerCase(), birthDate: birthDate! },
  };
}
