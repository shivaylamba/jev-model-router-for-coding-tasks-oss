import { isEmpty, normalizeSelection, replaceRange, type Selection } from "./text.ts";

export interface EditorOptions {
  /** Milliseconds clock used by undo grouping. Defaults to Date.now. */
  clock?: () => number;
  /** Maximum number of undo steps kept. Defaults to 100. */
  historyLimit?: number;
}

export class Editor {
  private content: string;
  private sel: Selection;

  constructor(text: string = "", options: EditorOptions = {}) {
    this.content = text;
    this.sel = { start: text.length, end: text.length };
    void options;
  }

  get text(): string {
    return this.content;
  }

  /** A copy of the current selection. */
  get selection(): Selection {
    return { ...this.sel };
  }

  /** Set the selection; offsets are clamped to the text and ordered. `end` defaults to `start`. */
  select(start: number, end: number = start): void {
    this.sel = normalizeSelection(this.content.length, start, end);
  }

  /** Replace the selection with `str` and put the cursor right after it. */
  insert(str: string): void {
    const { start, end } = this.sel;
    this.content = replaceRange(this.content, start, end, str);
    const cursor = start + str.length;
    this.sel = { start: cursor, end: cursor };
  }

  /** Delete the selection, or the character before the cursor when the selection is empty. */
  deleteBackward(): void {
    const { start, end } = this.sel;
    if (!isEmpty(this.sel)) {
      this.content = replaceRange(this.content, start, end, "");
      this.sel = { start, end: start };
    } else if (start > 0) {
      this.content = replaceRange(this.content, start - 1, start, "");
      this.sel = { start: start - 1, end: start - 1 };
    }
  }

  /** Delete the selection, or the character after the cursor when the selection is empty. */
  deleteForward(): void {
    const { start, end } = this.sel;
    if (!isEmpty(this.sel)) {
      this.content = replaceRange(this.content, start, end, "");
      this.sel = { start, end: start };
    } else if (start < this.content.length) {
      this.content = replaceRange(this.content, start, start + 1, "");
    }
  }
}
