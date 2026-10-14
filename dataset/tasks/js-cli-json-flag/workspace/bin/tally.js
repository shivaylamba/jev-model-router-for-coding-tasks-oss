#!/usr/bin/env node
import { readFileSync } from "node:fs";
import { run } from "../src/cli.js";

process.exitCode = run(process.argv.slice(2), {
  readFile: (path) => readFileSync(path, "utf8"),
  stdout: (text) => process.stdout.write(text),
  stderr: (text) => process.stderr.write(text),
});
