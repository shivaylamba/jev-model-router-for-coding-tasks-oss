export type Json = null | boolean | number | string | Json[] | { [key: string]: Json };

export type SchemaObject = { [keyword: string]: unknown };

export type Schema = boolean | SchemaObject;

export interface ValidationError {
  /** JSON Pointer to the offending location in the validated data ("" is the root). */
  path: string;
  /** The schema keyword that failed. */
  keyword: string;
}

/** Thrown when the schema itself cannot be used (for example an unresolvable $ref). */
export class SchemaError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "SchemaError";
  }
}
