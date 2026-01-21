import CodeMirror from 'codemirror';

const INDENT = '  ';

const BRACKET_PAIRS: Record<string, string> = {
  '{': '}',
  '[': ']',
  '(': ')',
  '"': '"',
  "'": "'",
};

/**
 * Checks if the cursor is currently inside a String or Comment token.
 * Used to prevent auto-closing brackets when typing text inside strings.
 *
 * @example
 * - Code: {"key": "valu|e"} -> Returns TRUE (Inside string)
 * - Code: // comm|ent      -> Returns TRUE (Inside comment)
 * - Code: {"key": | }      -> Returns FALSE
 */
const isCursorInStringOrComment = (cm: CodeMirror.Editor): boolean => {
  const cursor = cm.getCursor();
  const token = cm.getTokenAt(cursor);

  // token.type can be null, "string", "comment", or "variable", etc.
  return !!(
    token.type &&
    (token.type.indexOf('string') > -1 || token.type.indexOf('comment') > -1)
  );
};

/**
 * Handles opening brackets/quotes: {, [, (, ", '
 * Features: Auto-close, Selection Wrapping, String Safety, and Quote escaping.
 * Uses `cm.operation` to ensure Atomic Undo (1 Ctrl+Z undoes the whole action).
 *
 * @example
 * 1. Auto-Close:
 * Input:  |      + '{'
 * Result: { | }
 *
 * 2. Selection Wrap:
 * Input:  |text| + '['
 * Result: [text]
 *
 * 3. String Safety (No auto-close):
 * Input:  "Error: |" + '{'
 * Result: "Error: {"
 *
 * 4. Quote Skip (Type-over):
 * Input:  "value"|   + '"'
 * Result: "value"|   (Moves cursor right, doesn't add "")
 *
 * 5. Quote Escape (Important Edge Case):
 * Input:  "Escape \"|   + '"'
 * Result: "Escape \""|  (Inserts " because previous char was \)
 */
const handleOpen = (open: string, close: string) => (cm: CodeMirror.Editor) => {
  cm.operation(() => {
    // Logic Overwrite for Quotes (Skip if already exists)
    if (open === "'" || open === '"') {
      const cursor = cm.getCursor();
      const lineText = cm.getLine(cursor.line);
      const nextChar = lineText.charAt(cursor.ch);
      const prevChar = lineText.charAt(cursor.ch - 1);

      // Edge Case: If the previous character is '\\' (Escape) -> Do not skip the quote.
      // Example: Want to type "abc\" -> Do not skip the closing quote.
      if (nextChar === open && prevChar !== '\\') {
        cm.execCommand('goCharRight');
        return;
      }
    }

    // Logic Wrap Selection
    if (cm.somethingSelected()) {
      const selection = cm.getSelection();
      cm.replaceSelection(open + selection + close);
      return;
    }

    // Logic String/Comment
    if (isCursorInStringOrComment(cm)) {
      cm.replaceSelection(open);
      return;
    }

    // Default: Self-close and move cursor back
    cm.replaceSelection(open + close);
    cm.execCommand('goCharLeft');
  });
};

/**
 * Handles closing brackets: }, ], )
 * Implements "Type-over" logic: If the user types a closing bracket that already exists,
 * just move the cursor past it instead of duplicating it.
 *
 * @example
 * 1. Type-over (Skip):
 * Input:  { "a": 1 |}  + '}'
 * Result: { "a": 1 }|  (Cursor moved right)
 *
 * 2. Normal Insert:
 * Input:  { "a": 1 |   + '}'
 * Result: { "a": 1 }|
 */
const handleClose = (close: string) => (cm: CodeMirror.Editor) => {
  cm.operation(() => {
    const cursor = cm.getCursor();
    const nextChar = cm.getRange(cursor, {line: cursor.line, ch: cursor.ch + 1});

    // If the next character is the same as the closing bracket -> Skip
    if (nextChar === close) {
      cm.execCommand('goCharRight');
      return;
    }

    // Default: Print out
    cm.replaceSelection(close);
  });
};

/**
 * Handles Backspace key.
 * If the cursor is between a matching pair (e.g., "{|}"), deleting the open bracket
 * will automatically delete the closing bracket as well.
 *
 * @example
 * Input:  { | }   + Backspace
 * Result: |       (Both brackets removed)
 *
 * Input:  " | "   + Backspace
 * Result: |
 */
const handleBackspace = (cm: CodeMirror.Editor) => {
  if (cm.somethingSelected()) {
    return CodeMirror.Pass;
  }

  const cursor = cm.getCursor();
  // Get the character before and after the cursor
  const beforeCursor = cm.getRange({line: cursor.line, ch: cursor.ch - 1}, cursor);
  const afterCursor = cm.getRange(cursor, {line: cursor.line, ch: cursor.ch + 1});

  // If the characters before and after the cursor match a pair -> Delete both
  if (BRACKET_PAIRS[beforeCursor] === afterCursor) {
    cm.operation(() => {
      cm.replaceRange(
        '',
        {line: cursor.line, ch: cursor.ch - 1},
        {line: cursor.line, ch: cursor.ch + 1},
      );
    });
    return;
  }

  return CodeMirror.Pass;
};

/**
 * Handles Enter key (Smart Indent / Explode Brackets).
 *
 * @example
 * 1. Explode (Between brackets):
 * Input:  {| }    + Enter
 * Result:
 * {
 * |  <-- Indented
 * }
 *
 * 2. Regular Indent (After open bracket):
 * Input:  { |     + Enter
 * Result:
 * {
 * |
 *
 * 3. Default (Inside string/comment):
 * Input:  "Line 1|"  + Enter
 * Result:
 * "Line 1
 * |
 */
const handleEnter = (cm: CodeMirror.Editor) => {
  // If something is selected or the cursor is inside a string or comment -> Default behavior
  if (cm.somethingSelected() || isCursorInStringOrComment(cm)) {
    return CodeMirror.Pass;
  }

  const cursor = cm.getCursor();
  // cm.getLine can return undefined, fallback to ''
  const line = cm.getLine(cursor.line) || '';
  const beforeCursor = line.substring(0, cursor.ch);
  const afterCursor = line.substring(cursor.ch);

  // Check if between { } or [ ]
  if (
    (beforeCursor.trimEnd().endsWith('{') && afterCursor.trimStart().startsWith('}')) ||
    (beforeCursor.trimEnd().endsWith('[') && afterCursor.trimStart().startsWith(']'))
  ) {
    cm.operation(() => {
      const indent = beforeCursor.match(/^\s*/)?.[0] ?? '';
      const newIndent = indent + INDENT;

      // Insert: Newline + Indent deeper + Newline + Indent original
      cm.replaceSelection('\n' + newIndent + '\n' + indent, 'end');

      // Set cursor to middle line
      cm.setCursor({line: cursor.line + 1, ch: newIndent.length});
    });
    return;
  }

  // Check if after { or [
  if (beforeCursor.trimEnd().endsWith('{') || beforeCursor.trimEnd().endsWith('[')) {
    cm.operation(() => {
      const indent = beforeCursor.match(/^\s*/)?.[0] ?? '';
      const newIndent = indent + INDENT;
      cm.replaceSelection('\n' + newIndent);
    });
    return;
  }

  // Mặc định
  cm.execCommand('newlineAndIndent');
};

export const createJsonExtraKeys = (): CodeMirror.KeyMap => ({
  Enter: handleEnter,
  Tab: (cm: CodeMirror.Editor) => cm.execCommand('indentMore'),
  'Shift-Tab': (cm: CodeMirror.Editor) => cm.execCommand('indentLess'),
  Backspace: handleBackspace,

  // OVERRIDES
  "'{'": handleOpen('{', '}'),
  "'['": handleOpen('[', ']'),
  "'('": handleOpen('(', ')'),

  // Syntax for single quote key must be escaped
  "'''": handleOpen("'", "'"),
  "'\"'": handleOpen('"', '"'),

  // Close logic (Type-over)
  "'}'": handleClose('}'),
  "']'": handleClose(']'),
  "')'": handleClose(')'),
});
