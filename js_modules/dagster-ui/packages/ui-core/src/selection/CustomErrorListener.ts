import {ANTLRErrorListener, RecognitionException, Recognizer} from 'antlr4ts';
import {Token} from 'antlr4ts/Token';

export interface SyntaxError {
  message: string;
  line: number;
  column: number;
  offendingSymbol: Token | null;
}

export class CustomErrorListener implements ANTLRErrorListener<any> {
  private errors: SyntaxError[];

  constructor() {
    this.errors = [];
  }

  syntaxError(
    _recognizer: Recognizer<any, any>,
    offendingSymbol: any,
    line: number,
    charPositionInLine: number,
    msg: string,
    _e: RecognitionException | undefined,
  ): void {
    this.errors.push({
      message: msg,
      line,
      column: charPositionInLine,
      offendingSymbol,
    });
  }

  getErrors(): SyntaxError[] {
    return this.errors;
  }
}
