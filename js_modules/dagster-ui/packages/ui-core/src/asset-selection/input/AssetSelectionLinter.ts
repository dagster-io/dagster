import {CharStreams, CommonTokenStream} from 'antlr4ts';
import CodeMirror from 'codemirror';

import {SyntaxErrorListener} from './AssetSelectionSyntaxErrorListener';
import {AssetSelectionLexer} from '../generated/AssetSelectionLexer';
import {AssetSelectionParser} from '../generated/AssetSelectionParser';

export const lintAssetSelection = (text: string) => {
  const inputStream = CharStreams.fromString(text);
  const lexer = new AssetSelectionLexer(inputStream);
  const tokens = new CommonTokenStream(lexer);
  const parser = new AssetSelectionParser(tokens);

  const errorListener = new SyntaxErrorListener();
  parser.removeErrorListeners(); // Remove default console error listener
  parser.addErrorListener(errorListener);

  // Attempt to parse the input
  parser.start(); // Assuming 'start' is the entry point of your grammar

  // Map syntax errors to CodeMirror's lint format
  const lintErrors = errorListener.errors.map((error) => ({
    message: error.message.replace('<EOF>, ', ''),
    severity: 'error',
    from: CodeMirror.Pos(error.line, error.column),
    to: CodeMirror.Pos(error.line, text.length),
  }));

  return lintErrors;
};
