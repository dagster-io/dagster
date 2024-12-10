import {CharStreams, CommonTokenStream} from 'antlr4ts';
import CodeMirror from 'codemirror';

import {AssetSelectionSyntaxErrorListener} from './AssetSelectionSyntaxErrorListener';
import {AssetSelectionLexer} from '../generated/AssetSelectionLexer';
import {AssetSelectionParser} from '../generated/AssetSelectionParser';

export const lintAssetSelection = (text: string) => {
  const errorListener = new AssetSelectionSyntaxErrorListener();

  const inputStream = CharStreams.fromString(text);
  const lexer = new AssetSelectionLexer(inputStream);

  lexer.removeErrorListeners();
  lexer.addErrorListener(errorListener);

  const tokens = new CommonTokenStream(lexer);
  const parser = new AssetSelectionParser(tokens);

  parser.removeErrorListeners(); // Remove default console error listener
  parser.addErrorListener(errorListener);

  parser.start();

  // Map syntax errors to CodeMirror's lint format
  const lintErrors = errorListener.errors.map((error) => ({
    message: error.message.replace('<EOF>, ', ''),
    severity: 'error',
    from: CodeMirror.Pos(error.line, error.column),
    to: CodeMirror.Pos(error.line, text.length),
  }));

  return lintErrors;
};
