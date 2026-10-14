/**
 * Build the invitation payloads for a list of already-validated addresses.
 * @param {string[]} emails
 * @param {string} teamId
 */
export function buildInvites(emails, teamId) {
  return emails.map((email) => ({ to: email, teamId, kind: "team-invite" }));
}
