import {BaseErrorListener, RecognitionException, Token} from 'antlr4ng';

export class AntlrInputErrorListener extends BaseErrorListener {
  override syntaxError(
    _recognizer: unknown,
    offendingSymbol: Token | null,
    _line: number,
    charPositionInLine: number,
    msg: string,
    _e: RecognitionException | null,
  ): void {
    if (offendingSymbol) {
      throw new Error(`Syntax error caused by "${offendingSymbol.text}": ${msg}`);
    }
    throw new Error(`Syntax error at char ${charPositionInLine}: ${msg}`);
  }
}
