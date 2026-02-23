import CodeMirror from 'codemirror';

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
    const prevChar = editor.getRange({line: cursor.line, ch: cursor.ch - 1}, cursor);
    const nextChar = editor.getRange(cursor, {line: cursor.line, ch: cursor.ch + 1});

    const isBetweenBraces = prevChar === '{' && nextChar === '}';
    const isBetweenSquare = prevChar === '[' && nextChar === ']';

    if (isBetweenBraces || isBetweenSquare) {
      const line = editor.getLine(cursor.line);
      const baseIndent = line.match(/^\s*/)?.[0] || '';
      const indentUnit = editor.getOption('indentUnit') || 2;
      const innerIndent = baseIndent + ' '.repeat(indentUnit);

      editor.replaceSelection('\n' + innerIndent + '\n' + baseIndent);
      editor.setCursor({line: cursor.line + 1, ch: innerIndent.length});
      return undefined;
    }

    return CodeMirror.Pass;
  },
});
