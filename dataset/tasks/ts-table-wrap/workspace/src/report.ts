import { formatBytes, formatCount } from "./format.ts";
import { renderTable } from "./table.ts";

export interface PackageEntry {
  name: string;
  sizeBytes: number;
  downloads: number;
  description: string;
}

/** The package listing printed by `pkgls`, fitted to the terminal width. */
export function packageReport(entries: readonly PackageEntry[], terminalWidth: number): string {
  const rows = [
    ["Package", "Size", "Downloads", "Description"],
    ...entries.map((e) => [e.name, formatBytes(e.sizeBytes), formatCount(e.downloads), e.description]),
  ];
  return renderTable(rows, {
    maxWidth: terminalWidth,
    align: ["left", "right", "right", "left"],
    header: true,
  });
}
