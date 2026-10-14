# tinyschema specification

`validate(schema, data): ValidationError[]` checks a JSON value (`data`) against
a schema and returns every error found. An empty array means the value is
valid. `data` is always a JSON value: `null`, a boolean, a finite number, a
string, an array or a plain object.

```ts
interface ValidationError {
  path: string;    // JSON Pointer to the offending location in data
  keyword: string; // the schema keyword that failed
}
```

The order of the returned errors is not specified, but the list contains no
duplicates: the same `{ path, keyword }` pair appears at most once.

## Schemas

A schema is either a boolean or an object.

- `true` accepts everything. `false` rejects everything and reports one error
  at the current path with keyword `"false"`.
- An object schema applies each keyword it contains. Keywords are independent:
  every keyword is checked, and a failure of one does not stop the others.
  Keywords not listed in this document are ignored. An empty object accepts
  everything.

## Paths

`path` is a JSON Pointer (RFC 6901) into `data`. The root is `""`. An object
member adds `/` plus the member name with `~` written as `~0` and `/` written
as `~1`; an array element adds `/` plus its index. For example the member `a/b`
of the element at index 2 of the root array is `/2/a~1b`.

## Equality

`enum`, `const` and `uniqueItems` compare JSON values deeply: values of
different JSON types are never equal; arrays are equal when they have the same
length and equal elements in the same order; objects are equal when they have
the same set of member names and equal values for each name, regardless of
member order.

## Keywords

Each failing keyword reports one error at the current path unless stated
otherwise.

### Any type

- `type`: a type name or an array of names. Names: `"null"`, `"boolean"`,
  `"object"`, `"array"`, `"number"`, `"string"`, `"integer"`. `"number"`
  matches every number; `"integer"` matches numbers with no fractional part
  (so `2.0`, which is the same JSON number as `2`, is an integer). An array
  matches when any of its names matches. Arrays are not objects and `null` is
  not an object.
- `enum`: an array; the value must equal at least one element.
- `const`: the value must equal it.

### Numbers (ignored for non-numbers)

- `minimum` / `maximum`: value >= minimum, value <= maximum.
- `exclusiveMinimum` / `exclusiveMaximum` (numbers): value > exclusiveMinimum,
  value < exclusiveMaximum.

### Strings (ignored for non-strings)

- `minLength` / `maxLength`: length counted in Unicode code points, so an emoji
  such as "😀" (two UTF-16 code units) has length 1.
- `pattern`: a regular expression source, compiled with the `u` flag. It is not
  anchored: the string is valid when the expression matches anywhere in it.

### Objects (ignored for non-objects)

- `required`: an array of member names. Each missing member reports its own
  error, with keyword `"required"` and the path of the missing member (the
  object's path plus the member name), e.g. `/user/email`.
- `properties`: an object mapping member names to schemas. Each member present
  in the value is validated against its schema at the member's path. Errors
  come from those schemas; `properties` itself reports nothing.
- `additionalProperties`: applies to members whose name is not a key of
  `properties` in the same schema object (when `properties` is absent, to every
  member). `false` reports one error per such member, keyword
  `"additionalProperties"`, at the member's path. A schema validates each such
  member at its path and reports the resulting errors. `true` does nothing.

### Arrays (ignored for non-arrays)

- `minItems` / `maxItems`: bounds on the length.
- `items`: a schema; every element is validated against it at its index path.
- `uniqueItems`: when `true`, no two elements may be equal. One error at the
  array's path, no matter how many duplicates.

### Combining schemas

- `allOf`: an array of schemas; the value is validated against each of them and
  all of their errors are reported as they are. `allOf` itself reports nothing
  extra.
- `anyOf`: an array of schemas; the value must be valid against at least one.
  On failure, report a single error with keyword `"anyOf"` at the current path
  and none of the subschemas' errors.
- `oneOf`: an array of schemas; the value must be valid against exactly one.
  When none or more than one match, report a single error with keyword
  `"oneOf"` at the current path and none of the subschemas' errors.

### References

- `$ref`: a string `"#"` or `"#/..."`, a JSON Pointer into the root schema (the
  schema passed to `validate`). Each token selects an object member, or an
  element index when the current value is an array, and tokens are decoded
  with `~1` to `/` and `~0` to `~` (decode `~1` first). The value is validated against the referenced
  schema at the current path and its errors are reported as if that schema
  were written in place. Other keywords next to `$ref` still apply. References
  may be recursive (a tree schema referring to itself).
- A `$ref` that does not start with `#`, or that points to nothing, makes
  `validate` throw `SchemaError` (from `src/types.ts`) when it is reached.
