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
      // If the error is at the very end of the input, set the from to the start of the input
      from = 0;
    }
    this.errors.push({
      message: msg,
      offendingSymbol: offendingSymbol?.text,
      from,
      to: Infinity, //  Make the error span the rest of the input to make sure its pronounced
    });
  }

  getErrors(): SyntaxError[] {
    return this.errors;
  }
}
