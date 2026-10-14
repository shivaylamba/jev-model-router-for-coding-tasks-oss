import type { Selection } from "./text.ts";

/** The text and selection at one moment. */
export interface EditorState {
  text: string;
  selection: Selection;
}

/** One undo step. */
export interface Step {
  before: EditorState;
  after: EditorState;
}

/** Typing inserts extend the open group while each comes less than this many ms after the previous one. */
export const TYPING_GROUP_MS = 1000;

export class History {
  private readonly limit: number;
  private undoStack: Step[] = [];
  private redoStack: Step[] = [];
  private openGroup: Step | null = null;
  private lastTypingAt = 0;

  constructor(limit: number) {
    if (!Number.isInteger(limit) || limit < 0) {
      throw new RangeError("historyLimit must be an integer >= 0");
    }
    this.limit = limit;
  }

  canUndo(): boolean {
    return this.undoStack.length > 0;
  }

  canRedo(): boolean {
    return this.redoStack.length > 0;
  }

  /** Close the open typing group, if any. */
  closeGroup(): void {
    this.openGroup = null;
  }

  /**
   * Record a change. A typing change extends the open typing group when it is
   * still the latest step and the previous keystroke was less than
   * TYPING_GROUP_MS ago; otherwise it creates a new step.
   */
  record(before: EditorState, after: EditorState, typing: boolean, now: number): void {
    this.redoStack = [];
    const group = this.openGroup;
    if (
      typing &&
      group !== null &&
      this.undoStack[this.undoStack.length - 1] === group &&
      now - this.lastTypingAt < TYPING_GROUP_MS
    ) {
      group.after = after;
      this.lastTypingAt = now;
      return;
    }
    const step: Step = { before, after };
    this.undoStack.push(step);
    while (this.undoStack.length > this.limit) this.undoStack.shift();
    this.openGroup = typing ? step : null;
    if (typing) this.lastTypingAt = now;
  }

  /** Move the latest step to the redo stack and return it, or null. */
  undo(): Step | null {
    this.closeGroup();
    const step = this.undoStack.pop();
    if (!step) return null;
    this.redoStack.push(step);
    return step;
  }

  /** Move the latest undone step back to the undo stack and return it, or null. */
  redo(): Step | null {
    this.closeGroup();
    const step = this.redoStack.pop();
    if (!step) return null;
    this.undoStack.push(step);
    return step;
  }
}
