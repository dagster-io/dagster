import {ANTLRErrorListener, Parser, RecognitionException, Recognizer} from 'antlr4ts';

export type SyntaxError = {
  message: string;
  from: number;
  to: number;
} & (
  | {
      mismatchedInput?: undefined;
      expectedInput?: undefined;
    }
  | {
      mismatchedInput: string;
      expectedInput: string[];
    }
);

export class CustomErrorListener implements ANTLRErrorListener<any> {
  private errors: SyntaxError[];
  private parser: Parser | undefined;

  constructor({parser}: {parser?: Parser}) {
    this.parser = parser;
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
    const expectedTokens = this.parser?.getExpectedTokens()?.toArray();
    const message = msg;
    let mismatchedInput;
    let expectedInput;
    if (this.parser && expectedTokens?.length && expectedTokens[0] !== -1 && offendingSymbol) {
      mismatchedInput = offendingSymbol.text;
      expectedInput = expectedTokens
        .map((token) => this.parser?.vocabulary.getLiteralName(token))
        .filter(Boolean) as string[];
    }

    this.errors.push({
      message,
      from: charPositionInLine,
      to: charPositionInLine + (offendingSymbol?.text?.length ?? Infinity),
      mismatchedInput,
      expectedInput,
    });
  }

  getErrors(): SyntaxError[] {
    return this.errors;
  }
}
