import {
  ANTLRErrorListener,
  CharStreams,
  CommonTokenStream,
  RecognitionException,
  Recognizer,
} from 'antlr4ts';

import {AntlrAssetSelectionVisitor} from './AntlrAssetSelectionVisitor';
import {AssetGraphQueryItem} from '../asset-graph/useAssetGraphData';
import {AssetSelectionLexer} from './generated/AssetSelectionLexer';
import {AssetSelectionParser} from './generated/AssetSelectionParser';

class AntlrInputErrorListener implements ANTLRErrorListener<any> {
  syntaxError(
    recognizer: Recognizer<any, any>,
    offendingSymbol: any,
    line: number,
    charPositionInLine: number,
    msg: string,
    e: RecognitionException | undefined,
  ): void {
    if (offendingSymbol) {
      throw new Error(`Syntax error caused by "${offendingSymbol.text}": ${msg}`);
    }
    throw new Error(`Syntax error at char ${charPositionInLine}: ${msg}`);
  }
}

export const parseAssetSelectionQuery = (
  all_assets: AssetGraphQueryItem[],
  query: string,
): AssetGraphQueryItem[] | Error => {
  try {
    const lexer = new AssetSelectionLexer(CharStreams.fromString(query));
    lexer.removeErrorListeners();
    lexer.addErrorListener(new AntlrInputErrorListener());

    const tokenStream = new CommonTokenStream(lexer);

    const parser = new AssetSelectionParser(tokenStream);
    parser.removeErrorListeners();
    parser.addErrorListener(new AntlrInputErrorListener());

    const tree = parser.start();

    const visitor = new AntlrAssetSelectionVisitor(all_assets);
    return [...visitor.visit(tree)];
  } catch (e) {
    return e as Error;
  }
};
