import {CharStreams, CommonTokenStream} from 'antlr4ts';

import {AntlrAssetSelectionVisitor} from './AntlrAssetSelectionVisitor';
import {AssetGraphQueryItem} from '../asset-graph/useAssetGraphData';
import {AssetSelectionLexer} from './generated/AssetSelectionLexer';
import {AssetSelectionParser} from './generated/AssetSelectionParser';

export const parseAssetSelectionQuery = (
  all_assets: AssetGraphQueryItem[],
  query: string,
): AssetGraphQueryItem[] => {
  const lexer = new AssetSelectionLexer(CharStreams.fromString(query));
  const tokenStream = new CommonTokenStream(lexer);
  const parser = new AssetSelectionParser(tokenStream);
  const tree = parser.start();

  const visitor = new AntlrAssetSelectionVisitor(all_assets);
  return [...visitor.visit(tree)];
};
