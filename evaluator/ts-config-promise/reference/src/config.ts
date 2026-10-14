import { readFile } from "node:fs/promises";

export type Config = {
  host: string;
  port: number;
  debug: boolean;
};

export type ConfigCallback = (err: Error | null, config?: Config) => void;

/** Thrown (or passed to the callback) when the file parses but holds bad values. */
export class ConfigError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ConfigError";
  }
}

export const DEFAULTS: Config = { host: "localhost", port: 8080, debug: false };

/** Merge parsed JSON over the defaults and check the values. */
export function applyDefaults(raw: unknown): Config {
  if (raw === null || typeof raw !== "object" || Array.isArray(raw)) {
    throw new ConfigError("config must be a JSON object");
  }
  const config = { ...DEFAULTS, ...(raw as Partial<Config>) };
  if (!Number.isInteger(config.port) || config.port < 1 || config.port > 65535) {
    throw new ConfigError(`invalid port: ${config.port}`);
  }
  if (typeof config.host !== "string" || config.host === "") {
    throw new ConfigError("host must be a non-empty string");
  }
  if (typeof config.debug !== "boolean") {
    throw new ConfigError("debug must be a boolean");
  }
  return config;
}

/**
 * Read and validate a JSON config file.
 *
 * Without a callback, returns a Promise that resolves with the config or
 * rejects with the error: a file-system error (for example ENOENT), a
 * SyntaxError for malformed JSON, or a ConfigError for bad values.
 *
 * With a callback (the older style), the callback is called exactly once
 * with (err) or (null, config) and nothing is returned.
 */
export function readConfig(path: string): Promise<Config>;
export function readConfig(path: string, callback: ConfigCallback): void;
export function readConfig(path: string, callback?: ConfigCallback): Promise<Config> | void {
  const result = load(path);
  if (callback === undefined) {
    return result;
  }
  result.then(
    (config) => callback(null, config),
    (err) => callback(err as Error),
  );
}

async function load(path: string): Promise<Config> {
  const text = await readFile(path, "utf8");
  return applyDefaults(JSON.parse(text));
}
