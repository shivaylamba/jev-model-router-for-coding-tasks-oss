// Plain-text table rendering. The rules are in SPEC.md.

export type Align = "left" | "right" | "center";

export interface TableOptions {
  maxWidth?: number;
  align?: Align[];
  header?: boolean;
}

export function renderTable(rows: string[][], options: TableOptions = {}): string {
  throw new Error("renderTable is not implemented yet");
}
