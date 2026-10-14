# plaintext-editor

The editing model behind our notes app's plain-text editor: a string, a
selection, and the editing commands the UI's key bindings call. Rendering lives
elsewhere.

- `src/text.ts`: pure string and selection helpers.
- `src/editor.ts`: the `Editor` class.
- `docs/UNDO.md`: how undo and redo work.

TypeScript, run directly by Node 24 through type stripping: only erasable
syntax works (no `enum`, `namespace` or constructor parameter properties) and
relative imports include the `.ts` extension. No dependencies.

Run the tests with `node --test`.
