# Undo and redo

The editor keeps an undo history so that `undo()` and `redo()` step through
changes the way users expect from a text editor.

## API

On `Editor`:

- `undo(): boolean` reverts the most recent undo step. Returns `false` (and does
  nothing) when there is nothing to undo.
- `redo(): boolean` re-applies the most recently undone step. Returns `false`
  (and does nothing) when there is nothing to redo.
- `canUndo(): boolean`, `canRedo(): boolean`.
- `transact<T>(fn: () => T): T` runs `fn` and returns its result; see
  Transactions.
- Options (second constructor argument): `clock` (milliseconds, default
  `Date.now`) and `historyLimit` (default 100). `historyLimit` must be an
  integer >= 0, otherwise the constructor throws `RangeError`.

## Steps

An undo step remembers the text and the selection before and after a change.
`undo()` sets the text and the selection back to the step's "before" state and
moves the step to the redo stack. `redo()` sets the text and the selection to
the step's "after" state and moves the step back to the undo stack.

## What creates a step

- `insert`, `deleteBackward` and `deleteForward` create a step when they change
  the text. A call that leaves the text unchanged (for example
  `deleteBackward()` with the cursor at offset 0, or `insert("")` with an empty
  selection) creates no step and leaves the redo stack alone.
- `select()` never creates a step and never clears the redo stack.
- Whenever a step is created or extended, the redo stack is cleared.
- The initial text passed to the constructor is not undoable.

## Typing groups

Typing a word should be undone as one step, not one character at a time.

- An `insert` is *typing* when the selection is empty and the inserted string
  is exactly one character (`str.length === 1`) other than `"\n"`. Every other
  insert (a paste of several characters, a newline, replacing a non-empty
  selection) is not typing and always creates its own step.
- A typing insert extends the most recent undo step, instead of creating a new
  one, when that step is an open typing group and less than 1000 ms (by
  `clock`) have passed since the previous typing insert in that group. Exactly
  1000 ms or more starts a new step. Because the time is measured from the
  previous keystroke, typing continuously keeps extending one group.
- An extended step keeps its original "before" state, and its "after" state
  becomes the state after the latest insert.
- A typing insert that does not extend a step starts a new typing group.
- The open group is closed by any call to `select`, `deleteBackward`,
  `deleteForward`, `undo`, `redo` or `transact`, and by any insert that is not
  typing, whether or not the call changes anything. A closed group is never
  extended again.

## Transactions

`transact(fn)` makes everything `fn` does a single undo step.

- The step's "before" state is the text and selection when `transact` was
  called, and its "after" state is the text and selection when `fn` returns.
- If the text when `fn` returns equals the text when it started, no step is
  created and the redo stack is left alone.
- Nested `transact` calls join the outermost one: only the outermost call
  creates a step.
- If `fn` throws, the text and selection are put back to what they were when
  that `transact` call started, no step is created for it, the redo stack is
  left alone, and the error is rethrown.
- Typing inside a transaction never extends a step from before it, and typing
  after it never extends the transaction's step.
- Calling `undo()` or `redo()` while a transaction is running throws `Error`.

## History limit

At most `historyLimit` steps are kept on the undo stack. When a new step would
exceed the limit, the oldest step is discarded. Extending a typing group does
not count as a new step. With `historyLimit: 0` nothing is ever undoable.
