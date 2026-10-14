import { History, type EditorState } from "./history.ts";
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
  private readonly clock: () => number;
  private readonly history: History;
  private transactionDepth = 0;

  constructor(text: string = "", options: EditorOptions = {}) {
    this.content = text;
    this.sel = { start: text.length, end: text.length };
    this.clock = options.clock ?? Date.now;
    this.history = new History(options.historyLimit ?? 100);
  }

  get text(): string {
    return this.content;
  }

  /** A copy of the current selection. */
  get selection(): Selection {
    return { ...this.sel };
  }

  private snapshot(): EditorState {
    return { text: this.content, selection: { ...this.sel } };
  }

  private restore(state: EditorState): void {
    this.content = state.text;
    this.sel = { ...state.selection };
  }

  private record(before: EditorState, typing: boolean): void {
    if (this.transactionDepth > 0 || this.content === before.text) return;
    this.history.record(before, this.snapshot(), typing, typing ? this.clock() : 0);
  }

  /** Set the selection; offsets are clamped to the text and ordered. `end` defaults to `start`. */
  select(start: number, end: number = start): void {
    this.history.closeGroup();
    this.sel = normalizeSelection(this.content.length, start, end);
  }

  /** Replace the selection with `str` and put the cursor right after it. */
  insert(str: string): void {
    const typing = isEmpty(this.sel) && str.length === 1 && str !== "\n";
    if (!typing) this.history.closeGroup();
    const before = this.snapshot();
    const { start, end } = this.sel;
    this.content = replaceRange(this.content, start, end, str);
    const cursor = start + str.length;
    this.sel = { start: cursor, end: cursor };
    this.record(before, typing);
  }

  /** Delete the selection, or the character before the cursor when the selection is empty. */
  deleteBackward(): void {
    this.history.closeGroup();
    const before = this.snapshot();
    const { start, end } = this.sel;
    if (!isEmpty(this.sel)) {
      this.content = replaceRange(this.content, start, end, "");
      this.sel = { start, end: start };
    } else if (start > 0) {
      this.content = replaceRange(this.content, start - 1, start, "");
      this.sel = { start: start - 1, end: start - 1 };
    }
    this.record(before, false);
  }

  /** Delete the selection, or the character after the cursor when the selection is empty. */
  deleteForward(): void {
    this.history.closeGroup();
    const before = this.snapshot();
    const { start, end } = this.sel;
    if (!isEmpty(this.sel)) {
      this.content = replaceRange(this.content, start, end, "");
      this.sel = { start, end: start };
    } else if (start < this.content.length) {
      this.content = replaceRange(this.content, start, start + 1, "");
    }
    this.record(before, false);
  }

  canUndo(): boolean {
    return this.history.canUndo();
  }

  canRedo(): boolean {
    return this.history.canRedo();
  }

  undo(): boolean {
    if (this.transactionDepth > 0) throw new Error("cannot undo during a transaction");
    const step = this.history.undo();
    if (!step) return false;
    this.restore(step.before);
    return true;
  }

  redo(): boolean {
    if (this.transactionDepth > 0) throw new Error("cannot redo during a transaction");
    const step = this.history.redo();
    if (!step) return false;
    this.restore(step.after);
    return true;
  }

  /** Run `fn` so that all of its edits become one undo step. See docs/UNDO.md. */
  transact<T>(fn: () => T): T {
    this.history.closeGroup();
    const before = this.snapshot();
    this.transactionDepth++;
    let result: T;
    try {
      result = fn();
    } catch (error) {
      this.transactionDepth--;
      this.restore(before);
      throw error;
    }
    this.transactionDepth--;
    this.history.closeGroup();
    if (this.transactionDepth === 0 && this.content !== before.text) {
      this.history.record(before, this.snapshot(), false, 0);
    }
    return result;
  }
}
