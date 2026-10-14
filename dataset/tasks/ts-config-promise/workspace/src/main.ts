import { readConfig } from "./config.ts";

const path = process.argv[2] ?? "devserver.json";

readConfig(path, (err, config) => {
  if (err) {
    console.error(`could not load ${path}: ${err.message}`);
    process.exitCode = 1;
    return;
  }
  console.log(`serving on http://${config!.host}:${config!.port}${config!.debug ? " (debug)" : ""}`);
});
