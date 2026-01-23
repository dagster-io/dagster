import CodeMirror from 'codemirror';

/**
 * Type error for lint
 */
type CodemirrorLintError = {
  message: string;
  severity: 'error' | 'warning';
  from: CodeMirror.Position;
  to: CodeMirror.Position;
};

/**
 * Custom JSON Linter
 */
export const registerJsonLint = (): void => {
  // Use type assertion with interface extension for registration check
  interface CodeMirrorHelpers {
    helpers?: {
      lint?: {
        json?: unknown;
      };
    };
  }
  const cmHelpers = CodeMirror as unknown as CodeMirrorHelpers;

  // Avoid registering multiple times
  if (cmHelpers.helpers?.lint?.json) {
    return;
  }

  CodeMirror.registerHelper(
    'lint',
    'json',
    (text: string, _options: unknown, editor: CodeMirror.Editor): Array<CodemirrorLintError> => {
      const lints: Array<CodemirrorLintError> = [];

      // Empty string => no lint
      if (!text.trim()) {
        return lints;
      }

      try {
        JSON.parse(text);
        // Parse success -> no lint
      } catch (e: unknown) {
        const error = e as Error;
        const message = error.message || 'Invalid JSON';
        const position = extractErrorPosition(text, message, editor);

        lints.push({
          message,
          severity: 'error',
          from: position.from,
          to: position.to,
        });
      }

      return lints;
    },
  );
};

/**
 * Extract error position from JSON error message
 */
function extractErrorPosition(
  text: string,
  errorMessage: string,
  editor: CodeMirror.Editor,
): {from: CodeMirror.Position; to: CodeMirror.Position} {
  const codeMirrorDoc = editor.getDoc();

  // Default: start of file
  let from: CodeMirror.Position = {line: 0, ch: 0};
  let to: CodeMirror.Position = {line: 0, ch: 0};

  // === PATTERN 1: "at position X" (Chrome/V8/Node) ===
  let match = errorMessage.match(/position (\d+)/i);

  if (match && match[1]) {
    const index = parseInt(match[1], 10);
    from = codeMirrorDoc.posFromIndex(index) as CodeMirror.Position;
    to = codeMirrorDoc.posFromIndex(index + 1) as CodeMirror.Position;
    return {from, to};
  }

  // === PATTERN 2: "line X column Y" (Firefox) ===
  match = errorMessage.match(/line (\d+) column (\d+)/i);

  if (match && match[1] && match[2]) {
    const line = parseInt(match[1], 10) - 1;
    const ch = parseInt(match[2], 10) - 1;
    from = {line, ch};
    to = {line, ch: ch + 1};
    return {from, to};
  }

  // === PATTERN 3: Find error character ===
  match = errorMessage.match(/Unexpected token ['"]?(.?)['"]?/i);

  if (match && match[1]) {
    const unexpectedChar = match[1];
    const index = text.indexOf(unexpectedChar);
    if (index !== -1) {
      from = codeMirrorDoc.posFromIndex(index) as CodeMirror.Position;
      to = codeMirrorDoc.posFromIndex(index + 1) as CodeMirror.Position;
      return {from, to};
    }
  }

  // Fallback: start of file
  return {from, to};
}

/**
 * Check if cursor is inside a string token
 * Uses CodeMirror's tokenizer to detect string context
 */
export const isInsideString = (editor: CodeMirror.Editor): boolean => {
  const cursor = editor.getCursor();
  const tokenType = editor.getTokenTypeAt(cursor);
  return tokenType !== null && /\bstring\b/.test(tokenType);
};

/**
 * Create smart auto-close bracket handler
 * Returns CodeMirror.Pass when inside string to let default behavior (single char)
 */
const createBracketHandler = (open: string, close: string) => {
  return (editor: CodeMirror.Editor): typeof CodeMirror.Pass | void => {
    if (isInsideString(editor)) {
      return CodeMirror.Pass; // Let default key handler insert single char
    }
    // Insert paired brackets and move cursor between them
    editor.replaceSelection(open + close);
    const cursor = editor.getCursor();
    editor.setCursor({line: cursor.line, ch: cursor.ch - 1});
  };
};

/**
 * Create extraKeys map for smart auto-close brackets
 * Handles: { } [ ] ( ) " "
 * Also triggers hints when typing { inside strings
 */
export const createSmartBracketKeyMap = (): CodeMirror.KeyMap => ({
  // Special handler for { - triggers hints when inside strings
  "'{'": (editor: CodeMirror.Editor): typeof CodeMirror.Pass | void => {
    if (isInsideString(editor)) {
      // Inside string - insert { and trigger hints after a short delay
      editor.replaceSelection('{');
      // Use setTimeout to let the character be inserted first
      setTimeout(() => {
        editor.showHint({completeSingle: false});
      }, 50);
      return undefined;
    }
    // Outside string - insert paired brackets
    editor.replaceSelection('{}');
    const cursor = editor.getCursor();
    editor.setCursor({line: cursor.line, ch: cursor.ch - 1});
    return undefined;
  },
  "'['": createBracketHandler('[', ']'),
  "'('": createBracketHandler('(', ')'),

  // Quote handling for double quotes
  "'\"'": (editor: CodeMirror.Editor): typeof CodeMirror.Pass | void => {
    const cursor = editor.getCursor();
    const tokenType = editor.getTokenTypeAt(cursor);

    // Check next character - if it's the same quote, just move past it
    const nextChar = editor.getRange(cursor, {line: cursor.line, ch: cursor.ch + 1});
    if (nextChar === '"') {
      editor.setCursor({line: cursor.line, ch: cursor.ch + 1});
      return undefined;
    }

    // Inside string - insert single quote
    if (tokenType !== null && /\bstring\b/.test(tokenType)) {
      return CodeMirror.Pass;
    }

    // Outside string - insert paired quotes
    editor.replaceSelection('""');
    editor.setCursor({line: cursor.line, ch: cursor.ch + 1});
    return undefined;
  },

  // Enter key: auto-indent between brackets {} and []
  Enter: (editor: CodeMirror.Editor): typeof CodeMirror.Pass | void => {
    const cursor = editor.getCursor();

    // Get characters around cursor
    const prevChar = editor.getRange({line: cursor.line, ch: cursor.ch - 1}, cursor);
    const nextChar = editor.getRange(cursor, {line: cursor.line, ch: cursor.ch + 1});

    // Check if cursor is between matching brackets
    const isBetweenBraces = prevChar === '{' && nextChar === '}';
    const isBetweenSquare = prevChar === '[' && nextChar === ']';

    if (isBetweenBraces || isBetweenSquare) {
      // Get current line's indentation
      const line = editor.getLine(cursor.line);
      const baseIndent = line.match(/^\s*/)?.[0] || '';
      const indentUnit = editor.getOption('indentUnit') || 2;
      const innerIndent = baseIndent + ' '.repeat(indentUnit);

      // Insert: newline + inner indent + newline + base indent
      const insertion = '\n' + innerIndent + '\n' + baseIndent;
      editor.replaceSelection(insertion);

      // Move cursor to the middle line (indented position)
      editor.setCursor({line: cursor.line + 1, ch: innerIndent.length});
      return undefined;
    }

    // Not between brackets - use default Enter behavior
    return CodeMirror.Pass;
  },

  // Backspace: re-trigger hints if deletion leaves a { or {{ pattern in a string
  Backspace: (editor: CodeMirror.Editor): typeof CodeMirror.Pass | void => {
    // Note: We capture cursor before the backspace happens for potential future use
    const _cursor = editor.getCursor();

    // Perform the default backspace first
    const result = CodeMirror.Pass;

    // After a short delay, check if we should show hints
    setTimeout(() => {
      // Check if we're now in a string with a { pattern
      const newCursor = editor.getCursor();
      const tokenType = editor.getTokenTypeAt(newCursor);

      if (tokenType && /\bstring\b/.test(tokenType)) {
        const line = editor.getLine(newCursor.line);
        const textBeforeCursor = line.slice(0, newCursor.ch);

        // Check for { or {{ pattern (but not {{{ or more)
        const hasTokenPattern =
          /\{(\{[^{]|[^{])$/.test(textBeforeCursor) || /\{$/.test(textBeforeCursor);
        const hasTripleBrace = /\{\{\{+/.test(textBeforeCursor);

        if (hasTokenPattern && !hasTripleBrace) {
          editor.showHint({completeSingle: false});
        }
      }
    }, 50);

    return result;
  },
});
