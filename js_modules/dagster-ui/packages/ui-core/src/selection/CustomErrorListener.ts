import {ANTLRErrorListener, RecognitionException, Recognizer} from 'antlr4ts';

export type SyntaxError = {
  message: string;
  from: number;
  to: number;
  offendingSymbol?: string | null | undefined;
};

export class CustomErrorListener implements ANTLRErrorListener<any> {
  private errors: SyntaxError[];

  constructor() {
    this.errors = [];
  }

  syntaxError(
    _recognizer: Recognizer<any, any>,
    offendingSymbol: any,
    _line: number,
    charPositionInLine: number,
    msg: string,
    _e: RecognitionException | undefined,
  ): void {
    let from = charPositionInLine;
    if (offendingSymbol?.text === '<EOF>') {
      from = 0;
    }
    this.errors.push({
      message: msg,
      offendingSymbol: offendingSymbol?.text,
      from,
      to: charPositionInLine + (offendingSymbol?.text?.length ?? Infinity),
    });
  }

  getErrors(): SyntaxError[] {
    return this.errors;
  }
}
