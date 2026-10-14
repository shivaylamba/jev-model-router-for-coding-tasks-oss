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
