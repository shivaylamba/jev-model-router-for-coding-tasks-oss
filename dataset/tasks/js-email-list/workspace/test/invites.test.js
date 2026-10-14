import { test } from "node:test";
import assert from "node:assert/strict";
import { buildInvites } from "../src/invites.js";

test("buildInvites", () => {
  assert.deepEqual(buildInvites(["a@x.io"], "t1"), [{ to: "a@x.io", teamId: "t1", kind: "team-invite" }]);
});
