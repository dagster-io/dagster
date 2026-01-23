import CodeMirror from 'codemirror';

export interface JsonHintToken {
  name: string;
  description: string;
  example?: string;
}

/**
 * Hint options passed via editor.options.hintOptions
 */
export interface JsonHintOptions {
  tokens?: JsonHintToken[];
}

export type CodemirrorLocation = {
  line: number;
  ch: number;
};

export type CodemirrorHint = {
  render: (el: Element, self: CodeMirror.Hints, data: CodeMirror.Hint) => void;
  text: string;
  from: CodemirrorLocation;
  to: CodemirrorLocation;
};
/**
 * Find the token trigger position (looking for { or {{) in the current line
 * Returns the start position and the search string after the trigger
 * Returns null if triple brace ({{{) pattern is detected
 */
function findTokenTrigger(
  line: string,
  cursorCh: number,
): {start: number; searchString: string} | null {
  // Look backwards from cursor to find { or {{
  const textBeforeCursor = line.slice(0, cursorCh);

  // Triple brace guard: if there are 3+ consecutive { braces, don't show hints
  const tripleBraceMatch = textBeforeCursor.match(/\{\{\{+$/);
  if (tripleBraceMatch) {
    return null;
  }

  // Find the last { or {{ that starts a token
  let braceIndex = -1;
  let braceCount = 0;

  for (let i = textBeforeCursor.length - 1; i >= 0; i--) {
    if (textBeforeCursor[i] === '{') {
      braceCount++;
      if (braceIndex === -1) {
        braceIndex = i;
      }
    } else {
      // Stop if we hit a non-brace character
      break;
    }
  }

  // If 3 or more braces, don't show hints
  if (braceCount >= 3) {
    return null;
  }

  // If no brace found, check for token-in-progress (e.g., "{{job" after deletion)
  if (braceIndex === -1) {
    // Look for a token pattern like {{ followed by text
    const tokenInProgress = textBeforeCursor.match(/\{\{?([a-zA-Z0-9_.]*)$/);
    if (tokenInProgress) {
      braceIndex = textBeforeCursor.lastIndexOf(tokenInProgress[0]);
    }
  }

  if (braceIndex === -1) {
    return null;
  }

  // Extract the search string (text after {{ or {)
  const afterBrace = textBeforeCursor.slice(braceIndex);
  const searchString = afterBrace.replace(/^\{\{?/, '');

  return {start: braceIndex, searchString};
}

/**
 * Build a hint suggestion with custom rendering using CSS classes
 */
function buildHint(
  token: JsonHintToken,
  from: CodemirrorLocation,
  to: CodemirrorLocation,
  _searchString: string,
): CodemirrorHint {
  // Extract just the token name (remove {{ and }} if present)
  const tokenName = token.name.replace(/^\{\{|\}\}$/g, '');

  return {
    // Insert as {{token_name}} format
    text: `{{${tokenName}}}`,
    from,
    to,
    render: (el: Element) => {
      const container = document.createElement('div');
      container.className = 'cm-json-hint';

      // Token name row
      const nameRow = document.createElement('div');
      nameRow.style.display = 'flex';
      nameRow.style.alignItems = 'center';
      nameRow.style.gap = '8px';

      const name = document.createElement('span');
      name.className = 'cm-json-hint-name';
      name.textContent = `{{${tokenName}}}`;
      nameRow.appendChild(name);

      container.appendChild(nameRow);

      // Description
      if (token.description) {
        const desc = document.createElement('div');
        desc.className = 'cm-json-hint-description';
        desc.textContent =
          token.description.length > 80
            ? token.description.slice(0, 77) + '...'
            : token.description;
        container.appendChild(desc);
      }

      // Example value
      if (token.example) {
        const example = document.createElement('div');
        example.className = 'cm-json-hint-example';
        example.textContent = `Example: ${token.example}`;
        container.appendChild(example);
      }

      el.appendChild(container);
    },
  };
}

/**
 * Register JSON hint helper for token autocomplete
 * Only shows hints inside string values when typing { or {{
 */
export const registerJsonHint = (): void => {
  // Use type assertion with interface extension for registration check
  interface CodeMirrorExtended {
    _jsonHintRegistered?: boolean;
  }
  const cmExtended = CodeMirror as unknown as CodeMirrorExtended;

  // Avoid duplicate registration
  if (cmExtended._jsonHintRegistered) {
    return;
  }
  cmExtended._jsonHintRegistered = true;

  CodeMirror.registerHelper(
    'hint',
    'javascript',
    (
      editor: CodeMirror.Editor,
      options: JsonHintOptions,
    ): {list: CodemirrorHint[]; from: CodemirrorLocation; to: CodemirrorLocation} | null => {
      const cursor = editor.getCursor();
      const token = editor.getTokenAt(cursor);

      // Only show hints inside string values
      if (!token.type || !/\bstring\b/.test(token.type)) {
        return null;
      }

      const line = editor.getLine(cursor.line);
      const trigger = findTokenTrigger(line, cursor.ch);

      if (!trigger) {
        return null;
      }

      const tokens = options?.tokens || [];
      if (tokens.length === 0) {
        return null;
      }

      const from: CodemirrorLocation = {line: cursor.line, ch: trigger.start};
      const to: CodemirrorLocation = {line: cursor.line, ch: cursor.ch};

      // Filter tokens by search string
      const searchLower = trigger.searchString.toLowerCase();
      const filteredTokens = tokens.filter((t) => {
        const tokenName = t.name.replace(/^\{\{|\}\}$/g, '').toLowerCase();
        return tokenName.includes(searchLower) || t.description.toLowerCase().includes(searchLower);
      });

      if (filteredTokens.length === 0) {
        return null;
      }

      const hints = filteredTokens.map((t) => buildHint(t, from, to, trigger.searchString));

      return {list: hints, from, to};
    },
  );
};
