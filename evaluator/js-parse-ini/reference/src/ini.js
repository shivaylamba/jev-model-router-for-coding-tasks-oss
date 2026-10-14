/**
 * INI reading and writing. See docs/INI_FORMAT.md for the dialect.
 */

function quote(value) {
  const escaped = value
    .replace(/\\/g, "\\\\")
    .replace(/"/g, '\\"')
    .replace(/\n/g, "\\n")
    .replace(/\t/g, "\\t");
  return `"${escaped}"`;
}

function needsQuotes(value) {
  return value !== value.trim() || /["\\\n\t]/.test(value) || value.startsWith('"');
}

/**
 * Serialize { section: { key: value } } to INI text. Keys of the "" section
 * are written first, without a header. Values are converted with String().
 */
export function stringifyIni(data) {
  const lines = [];
  const sections = Object.keys(data);
  const ordered = sections.includes("") ? ["", ...sections.filter((s) => s !== "")] : sections;
  for (const section of ordered) {
    if (section !== "") {
      if (lines.length > 0) lines.push("");
      lines.push(`[${section}]`);
    }
    for (const [key, raw] of Object.entries(data[section])) {
      const value = String(raw);
      lines.push(`${key} = ${needsQuotes(value) ? quote(value) : value}`);
    }
  }
  return lines.join("\n") + "\n";
}

function fail(message, line) {
  const error = new SyntaxError(`line ${line}: ${message}`);
  error.line = line;
  return error;
}

const ESCAPES = { '"': '"', "\\": "\\", n: "\n", t: "\t" };

function parseQuoted(text, line) {
  let out = "";
  let i = 1;
  while (i < text.length) {
    const ch = text[i];
    if (ch === "\\") {
      const next = text[i + 1];
      if (next === undefined || !(next in ESCAPES)) throw fail("invalid escape", line);
      out += ESCAPES[next];
      i += 2;
    } else if (ch === '"') {
      if (text.slice(i + 1).trim() !== "") throw fail("text after closing quote", line);
      return out;
    } else {
      out += ch;
      i += 1;
    }
  }
  throw fail("unterminated quoted value", line);
}

/** Parse INI text into { section: { key: value } }. See docs/INI_FORMAT.md. */
export function parseIni(text) {
  const lines = text.split(/\r?\n/);
  const result = {};
  let section = "";
  for (let index = 0; index < lines.length; index += 1) {
    const lineNo = index + 1;
    const line = lines[index].trim();
    if (line === "" || line.startsWith(";") || line.startsWith("#")) continue;
    if (line.startsWith("[")) {
      if (!line.endsWith("]")) throw fail("unterminated section header", lineNo);
      const name = line.slice(1, -1).trim();
      if (name === "") throw fail("empty section name", lineNo);
      section = name;
      if (!Object.hasOwn(result, section)) result[section] = {};
      continue;
    }
    const eq = line.indexOf("=");
    if (eq === -1) throw fail("expected key = value", lineNo);
    const key = line.slice(0, eq).trim();
    if (key === "") throw fail("empty key", lineNo);
    let value = line.slice(eq + 1).trim();
    if (value.startsWith('"')) {
      value = parseQuoted(value, lineNo);
    } else {
      let startLine = lineNo;
      while (value.endsWith("\\")) {
        if (index + 1 >= lines.length) throw fail("continuation at end of file", startLine);
        index += 1;
        startLine = index + 1;
        value = `${value.slice(0, -1).trimEnd()} ${lines[index].trim()}`;
      }
    }
    if (!Object.hasOwn(result, section)) result[section] = {};
    result[section][key] = value;
  }
  return result;
}
