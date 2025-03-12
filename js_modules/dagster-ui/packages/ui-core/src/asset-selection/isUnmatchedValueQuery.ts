import {CharStreams, CommonTokenStream} from 'antlr4ts';
import {AbstractParseTreeVisitor} from 'antlr4ts/tree/AbstractParseTreeVisitor';

import {AntlrInputErrorListener} from './parseAssetSelectionQuery';
import {SelectionAutoCompleteLexer} from '../selection/generated/SelectionAutoCompleteLexer';
import {
  SelectionAutoCompleteParser,
  UnmatchedValueContext,
} from '../selection/generated/SelectionAutoCompleteParser';
import {SelectionAutoCompleteVisitor} from '../selection/generated/SelectionAutoCompleteVisitor';

class UnmatchedValueQueryVisitor
  extends AbstractParseTreeVisitor<void>
  implements SelectionAutoCompleteVisitor<void>
{
  public isUnmatchedValue: boolean;

  defaultResult() {}

  constructor(private query: string) {
    super();
    this.isUnmatchedValue = false;
  }

  visitUnmatchedValue(ctx: UnmatchedValueContext) {
    if (ctx.start.startIndex === 0 && ctx.stop?.stopIndex === this.query.length - 1) {
      // If a single attribute expression is the entire query, it's not a complex
      this.isUnmatchedValue = true;
    }
  }
}

export const isUnmatchedValueQuery = (query: string) => {
  try {
    const lexer = new SelectionAutoCompleteLexer(CharStreams.fromString(query));
    lexer.removeErrorListeners();
    lexer.addErrorListener(new AntlrInputErrorListener());

    const tokenStream = new CommonTokenStream(lexer);

    const parser = new SelectionAutoCompleteParser(tokenStream);
    parser.removeErrorListeners();
    parser.addErrorListener(new AntlrInputErrorListener());

    const tree = parser.start();

    const visitor = new UnmatchedValueQueryVisitor(query);
    visitor.visit(tree);
    return visitor.isUnmatchedValue;
  } catch {
    return false;
  }
};
