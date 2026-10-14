import { deepMerge } from "./merge.ts";

export type Config = Record<string, unknown>;

export const DEFAULTS: Config = {
  service: { name: "api", port: 8080 },
  db: { host: "localhost", port: 5432, pool: 5 },
  features: ["metrics"],
};

/** Layer overrides over the defaults, later layers winning. */
export function loadConfig(...layers: Array<Config | undefined>): Config {
  return deepMerge(DEFAULTS, ...layers);
}
