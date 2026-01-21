import {useMemo} from 'react';

export interface Position {
  line: number;
  ch: number;
}

export interface LintError {
  message: string;
  severity: 'error' | 'warning';
  from: Position;
  to: Position;
}

const ERROR_MESSAGES = {
  MUST_BE_OBJECT: 'JSON body must be an object {} or array [], not a primitive value',
  TRAILING_COMMA: 'Trailing comma is not allowed',
} as const;

const getPosFromIndex = (text: string, index: number): Position => {
  let line = 0;
  let curIndex = 0;
  let nextNewline = text.indexOf('\n');

  while (nextNewline !== -1 && nextNewline < index) {
    line++;
    curIndex = nextNewline + 1;
    nextNewline = text.indexOf('\n', curIndex);
  }
  return {line, ch: index - curIndex};
};

const extractErrorPosition = (error: Error, text: string): Position => {
  const msg = error.message;
  // Chrome/Node
  const posMatch = msg.match(/position (\d+)/);
  if (posMatch?.[1]) {
    return getPosFromIndex(text, parseInt(posMatch[1], 10));
  }
  // Firefox
  const lineColMatch = msg.match(/line (\d+) column (\d+)/);
  if (lineColMatch?.[1] && lineColMatch?.[2]) {
    return {
      line: parseInt(lineColMatch[1], 10) - 1,
      ch: parseInt(lineColMatch[2], 10) - 1,
    };
  }
  return {line: 0, ch: 0};
};

const cleanErrorMessage = (msg: string): string => {
  return msg
    .replace(/^JSON\.parse:\s*/i, '')
    .replace(/^Unexpected token\s+/i, 'Unexpected ')
    .replace(/\s+in JSON at position \d+/i, '')
    .replace(/\s+at position \d+/i, '')
    .trim();
};

export const useJsonValidator = () => {
  return useMemo(
    () =>
      (text: string): LintError[] => {
        if (!text.trim()) return [];

        // Regex Check for Trailing Comma (Faster than parsing)
        const trailingMatch = /,\s*([}\]])/.exec(text);
        if (trailingMatch) {
          const start = getPosFromIndex(text, trailingMatch.index);
          return [
            {
              message: ERROR_MESSAGES.TRAILING_COMMA,
              severity: 'error',
              from: start,
              to: {line: start.line, ch: start.ch + 1},
            },
          ];
        }

        // JSON.parse Check
        try {
          const parsed = JSON.parse(text);
          if (typeof parsed !== 'object' || parsed === null) {
            return [
              {
                message: ERROR_MESSAGES.MUST_BE_OBJECT,
                severity: 'error',
                from: {line: 0, ch: 0},
                to: getPosFromIndex(text, text.length),
              },
            ];
          }
          return [];
        } catch (err) {
          const error = err as Error;
          let finalMsg = cleanErrorMessage(error.message);
          const fromPos = extractErrorPosition(error, text);
          const lineText = text.split('\n')[fromPos.line] || '';

          // Smart Suggestion for missing quotes
          const charAtErr = lineText[fromPos.ch];
          if (
            charAtErr &&
            /[a-zA-Z0-9]/.test(charAtErr) &&
            !finalMsg.includes('Unexpected string')
          ) {
            finalMsg = `Unexpected token '${charAtErr}'. Keys must be double-quoted.`;
          }

          // Highlight logic
          let toCh = fromPos.ch;
          // Highlight the entire token
          while (toCh < lineText.length && !/[\s,:}\]]/.test(lineText[toCh] || '')) {
            toCh++;
          }

          return [
            {
              message: finalMsg,
              severity: 'error',
              from: fromPos,
              to: {...fromPos, ch: Math.max(toCh, fromPos.ch + 1)},
            },
          ];
        }
      },
    [],
  );
};
