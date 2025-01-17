import {CharStreams, CommonTokenStream, Lexer, Parser, ParserRuleContext} from 'antlr4ts';
import CodeMirror from 'codemirror';
import {Linter} from 'codemirror/addon/lint/lint';

import {CustomErrorListener} from './CustomErrorListener';

type LexerConstructor = new (...args: any[]) => Lexer;
type ParserConstructor = new (...args: any[]) => Parser & {
  start: () => ParserRuleContext;
};

export function createSelectionLinter({
  Lexer: LexerKlass,
  Parser: ParserKlass,
}: {
  Lexer: LexerConstructor;
  Parser: ParserConstructor;
}): Linter<any> {
  return (text: string) => {
    const errorListener = new CustomErrorListener();

    const inputStream = CharStreams.fromString(text);
    const lexer = new LexerKlass(inputStream);

    lexer.removeErrorListeners();
    lexer.addErrorListener(errorListener);

    const tokens = new CommonTokenStream(lexer);
    const parser = new ParserKlass(tokens);

    parser.removeErrorListeners(); // Remove default console error listener
    parser.addErrorListener(errorListener);

    parser.start();

    // Map syntax errors to CodeMirror's lint format
    const lintErrors = errorListener.getErrors().map((error) => ({
      message: error.message.replace('<EOF>, ', ''),
      severity: 'error',
      from: CodeMirror.Pos(0, error.column),
      to: CodeMirror.Pos(0, text.length),
    }));

    return lintErrors;
  };
}
