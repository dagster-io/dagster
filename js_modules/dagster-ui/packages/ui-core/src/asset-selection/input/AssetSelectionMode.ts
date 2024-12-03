import {CharStreams, Token, Vocabulary} from 'antlr4ts';
import {Mode} from 'codemirror';

import {AssetSelectionLexer} from '../generated/AssetSelectionLexer';

// Define an interface for the state to keep track of tokens and errors
interface AssetSelectionState {
  tokens: Token[];
  tokenIndex: number;
  errors: {start: number; end: number; message: string}[];
}

export function assetSelectionMode(): Mode<AssetSelectionState> {
  return {
    startState(): AssetSelectionState {
      return {
        tokens: [],
        tokenIndex: 0,
        errors: [],
      };
    },
    token(stream, state) {
      // Consume any whitespace at the current stream position
      while (/\s/.test(stream.peek() ?? '')) {
        stream.next();
      }

      // If all tokens have been processed, lex the rest of the line
      if (state.tokenIndex >= state.tokens.length) {
        // Read the rest of the line from the current position
        const currentLine = stream.string.slice(stream.pos);

        if (currentLine.length === 0) {
          // No more input to process
          return null;
        }

        try {
          // Create a CharStream from the current line
          const inputStream = CharStreams.fromString(currentLine);

          // Initialize the lexer with the input stream
          const lexer = new AssetSelectionLexer(inputStream);

          // Collect all tokens from the lexer
          const tokens: Token[] = [];
          let token = lexer.nextToken();
          while (token.type !== Token.EOF) {
            tokens.push(token);
            token = lexer.nextToken();
          }

          // Update the state with the new tokens
          state.tokens = tokens;
          state.tokenIndex = 0;
        } catch {
          // Advance the stream to the end, marking as error
          stream.skipToEnd();

          // Return the 'error' style
          return 'error';
        }
      }

      if (state.tokenIndex < state.tokens.length) {
        const token = state.tokens[state.tokenIndex++]!;
        const tokenText = token.text!;

        // Consume any whitespace before matching the token
        while (/\s/.test(stream.peek() ?? '')) {
          stream.next();
        }

        // Match the token text from the stream
        if (stream.match(tokenText)) {
          // Map the token type to a CodeMirror style
          const style = tokenTypeToStyle(token.type, AssetSelectionLexer.VOCABULARY);
          return style;
        } else {
          // If there's a mismatch, consume the rest of the line and mark as error
          stream.skipToEnd();
          return 'error';
        }
      } else {
        // No more tokens; skip to the end of the line
        stream.skipToEnd();
        return null;
      }
    },
  };
}

function tokenTypeToStyle(tokenType: number, vocabulary: Vocabulary): string | null {
  const tokenName = vocabulary.getSymbolicName(tokenType);
  switch (tokenName) {
    case 'KEY':
    case 'KEY_SUBSTRING':
    case 'TAG':
    case 'OWNER':
    case 'GROUP':
    case 'KIND':
    case 'CODE_LOCATION':
      return 'attribute';
    case 'AND':
    case 'OR':
    case 'NOT':
      return 'operator';
    case 'QUOTED_STRING':
    case 'UNQUOTED_STRING':
      return 'string';
    case 'SINKS':
    case 'ROOTS':
      return 'function';
    case 'STAR':
    case 'PLUS':
      return 'operator';
    case 'COLON':
    case 'EQUAL':
    case 'LPAREN':
    case 'RPAREN':
    case 'COMMA':
      return 'punctuation';
    case 'WS':
      return null;
    default:
      return 'error'; // Map any unknown tokens to 'error' style
  }
}
