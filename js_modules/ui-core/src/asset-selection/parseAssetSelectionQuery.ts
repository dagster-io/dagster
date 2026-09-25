import {AntlrAssetSelectionVisitor} from '@shared/asset-selection/AntlrAssetSelectionVisitor';
import {CharStream, CommonTokenStream} from 'antlr4ng';

import {SupplementaryInformation} from './types';
import {AssetGraphQueryItem} from '../asset-graph/types';
import {AssetSelectionLexer} from './generated/AssetSelectionLexer';
import {AssetSelectionParser} from './generated/AssetSelectionParser';
import {AntlrInputErrorListener} from '../selection/AntlrInputErrorListener';

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
    tokenStream.fill(); // Ensure all tokens are loaded before parsing

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
