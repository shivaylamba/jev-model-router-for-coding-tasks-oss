import { validateSignup } from "./signup.ts";

export interface Response {
  status: number;
  body: unknown;
}

/** Turn a sign-up request body into a response. `now` is injected by the server. */
export function handleSignup(body: unknown, now: Date): Response {
  const input = typeof body === "object" && body !== null ? (body as Record<string, unknown>) : {};
  const result = validateSignup(input, now);
  if (!result.ok) {
    return { status: 422, body: { errors: result.errors } };
  }
  return { status: 201, body: { username: result.value.username } };
}
