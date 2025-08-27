import {CharStreams, CommonTokenStream} from 'antlr4ts';
import {AbstractParseTreeVisitor} from 'antlr4ts/tree/AbstractParseTreeVisitor';

import {AssetSelectionLexer} from './generated/AssetSelectionLexer';
import {AssetSelectionParser, StatusAttributeExprContext} from './generated/AssetSelectionParser';
import {AssetSelectionVisitor} from './generated/AssetSelectionVisitor';
import {AntlrInputErrorListener} from './parseAssetSelectionQuery';
import {getValue} from './util';

export type Filter = {field: 'status'; value: string};

export class AssetSelectionSupplementaryDataVisitor
  extends AbstractParseTreeVisitor<void>
  implements AssetSelectionVisitor<void>
{
  public filters: Filter[] = [];

  constructor() {
    super();
  }

  protected defaultResult() {}

  visitStatusAttributeExpr(ctx: StatusAttributeExprContext) {
    const value: string = getValue(ctx.value()).toUpperCase();
    this.filters.push({field: 'status', value});
  }
}

export const parseExpression = (expression: string) => {
  if (expression === '') {
    return [];
  }

  const inputStream = CharStreams.fromString(expression);
  const lexer = new AssetSelectionLexer(inputStream);
  lexer.removeErrorListeners();
  lexer.addErrorListener(new AntlrInputErrorListener());

  const tokenStream = new CommonTokenStream(lexer);
  const parser = new AssetSelectionParser(tokenStream);
  parser.removeErrorListeners();
  parser.addErrorListener(new AntlrInputErrorListener());

  const tree = parser.start();
  const visitor = new AssetSelectionSupplementaryDataVisitor();
  tree.accept(visitor);
  return visitor.filters;
};
