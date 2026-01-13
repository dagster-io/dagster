import {CharStream, CommonTokenStream} from 'antlr4ng';

import {AntlrOpSelectionVisitor} from './AntlrOpSelectionVisitor';
import {GraphQueryItem} from '../app/GraphQueryImpl';
import {OpSelectionLexer} from './generated/OpSelectionLexer';
import {OpSelectionParser} from './generated/OpSelectionParser';
import {AntlrInputErrorListener} from '../asset-selection/parseAssetSelectionQuery';

type OpSelectionQueryResult<T extends GraphQueryItem> = {
  all: T[];
  focus: T[];
};

export const parseOpSelectionQuery = <T extends GraphQueryItem>(
  all_ops: T[],
  query: string,
): OpSelectionQueryResult<T> | Error => {
  try {
    const lexer = new OpSelectionLexer(CharStream.fromString(query));
    lexer.removeErrorListeners();
    lexer.addErrorListener(new AntlrInputErrorListener());

    const tokenStream = new CommonTokenStream(lexer);
    tokenStream.fill(); // Ensure all tokens are loaded before parsing

    const parser = new OpSelectionParser(tokenStream);
    parser.removeErrorListeners();
    parser.addErrorListener(new AntlrInputErrorListener());

    const tree = parser.start();

    const visitor = new AntlrOpSelectionVisitor(all_ops);
    const all_selection = visitor.visit(tree) ?? new Set<T>();
    const focus_selection = visitor.focus_ops;

    return {
      all: Array.from(all_selection),
      focus: Array.from(focus_selection),
    };
  } catch (e) {
    return e as Error;
  }
};

export const filterOpSelectionByQuery = <T extends GraphQueryItem>(
  all_ops: T[],
  query: string,
): OpSelectionQueryResult<T> => {
  if (query.length === 0) {
    return {all: all_ops, focus: []};
  }
  const result = parseOpSelectionQuery(all_ops, query);
  if (result instanceof Error) {
    return {all: [], focus: []};
  }
  return result;
};
