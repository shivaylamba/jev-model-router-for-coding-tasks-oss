export type SignupField = "username" | "email" | "password" | "confirmPassword" | "birthDate";

export type SignupErrorCode =
  | "required"
  | "length"
  | "format"
  | "weak"
  | "contains_username"
  | "mismatch"
  | "future"
  | "too_young";

export type SignupInput = Partial<Record<SignupField, unknown>>;

export type SignupErrors = Partial<Record<SignupField, SignupErrorCode>>;

export interface SignupValue {
  username: string;
  email: string;
  birthDate: string;
}

export type SignupResult = { ok: true; value: SignupValue } | { ok: false; errors: SignupErrors };
