import {BaseErrorListener, RecognitionException, Token} from 'antlr4ng';

export type SyntaxError = {
  message: string;
  from: number;
  to: number;
  offendingSymbol?: string | null | undefined;
};

export class CustomErrorListener extends BaseErrorListener {
  private errors: SyntaxError[];

  constructor() {
    super();
    this.errors = [];
  }

  override syntaxError(
    _recognizer: unknown,
    offendingSymbol: Token | null,
    _line: number,
    charPositionInLine: number,
    msg: string,
    _e: RecognitionException | null,
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
