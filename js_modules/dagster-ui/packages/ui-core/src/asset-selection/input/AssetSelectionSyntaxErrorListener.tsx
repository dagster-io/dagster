import {ANTLRErrorListener, RecognitionException, Recognizer} from 'antlr4ts';

interface SyntaxError {
  message: string;
  line: number;
  column: number;
}

export class SyntaxErrorListener implements ANTLRErrorListener<any> {
  public errors: SyntaxError[] = [];

  syntaxError<T>(
    _recognizer: Recognizer<T, any>,
    _offendingSymbol: T | undefined,
    line: number,
    charPositionInLine: number,
    msg: string,
    e: RecognitionException | undefined,
  ): void {
    this.errors.push({
      message: msg,
      line: line - 1, // CodeMirror lines are 0-based
      column: charPositionInLine,
    });
  }
}
