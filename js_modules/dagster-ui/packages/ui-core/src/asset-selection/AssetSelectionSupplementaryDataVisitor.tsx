import {CharStreams, CommonTokenStream} from 'antlr4ts';
import {AbstractParseTreeVisitor} from 'antlr4ts/tree/AbstractParseTreeVisitor';

import {AssetSelectionLexer} from './generated/AssetSelectionLexer';
import {AssetSelectionParser, StatusAttributeExprContext} from './generated/AssetSelectionParser';
import {AssetSelectionVisitor} from './generated/AssetSelectionVisitor';
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
    const value: string = getValue(ctx.value());
    this.filters.push({field: 'status', value});
  }
}

export const parseExpression = (expression: string) => {
  const inputStream = CharStreams.fromString(expression);
  const lexer = new AssetSelectionLexer(inputStream);
  const tokenStream = new CommonTokenStream(lexer);
  const parser = new AssetSelectionParser(tokenStream);
  const tree = parser.start();
  const visitor = new AssetSelectionSupplementaryDataVisitor();
  tree.accept(visitor);
  return visitor.filters;
};
