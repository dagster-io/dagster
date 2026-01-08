import {BaseErrorListener, CharStream, CommonTokenStream, RecognitionException, Token} from 'antlr4ng';
import {AntlrAssetSelectionVisitor} from 'shared/asset-selection/AntlrAssetSelectionVisitor.oss';

import {SupplementaryInformation} from './types';
import {AssetGraphQueryItem} from '../asset-graph/types';
import {AssetSelectionLexer} from './generated/AssetSelectionLexer';
import {AssetSelectionParser} from './generated/AssetSelectionParser';

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

export type AssetSelectionQueryResult = {
  all: AssetGraphQueryItem[];
  focus: AssetGraphQueryItem[];
};

export const parseAssetSelectionQuery = (
  all_assets: AssetGraphQueryItem[],
  query: string,
  supplementaryData?: SupplementaryInformation,
): AssetSelectionQueryResult | Error => {
  try {
    const lexer = new AssetSelectionLexer(CharStream.fromString(query));
    lexer.removeErrorListeners();
    lexer.addErrorListener(new AntlrInputErrorListener());

    const tokenStream = new CommonTokenStream(lexer);

    const parser = new AssetSelectionParser(tokenStream);
    parser.removeErrorListeners();
    parser.addErrorListener(new AntlrInputErrorListener());

    const tree = parser.start();

    const visitor = new AntlrAssetSelectionVisitor(all_assets, supplementaryData);

    const all_selection = visitor.visit(tree) ?? new Set<AssetGraphQueryItem>();
    const focus_selection = visitor.focus_assets;

    return {
      all: Array.from(all_selection),
      focus: Array.from(focus_selection),
    };
  } catch (e) {
    return e as Error;
  }
};
