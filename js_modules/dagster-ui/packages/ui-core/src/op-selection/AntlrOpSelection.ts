import {CharStreams, CommonTokenStream} from 'antlr4ts';
import {FeatureFlag} from 'shared/app/FeatureFlags.oss';

import {AntlrOpSelectionVisitor} from './AntlrOpSelectionVisitor';
import {GraphQueryItem, filterByQuery} from '../app/GraphQueryImpl';
import {AntlrInputErrorListener} from '../asset-selection/AntlrAssetSelection';
import {OpSelectionLexer} from './generated/OpSelectionLexer';
import {OpSelectionParser} from './generated/OpSelectionParser';
import {featureEnabled} from '../app/Flags';

type OpSelectionQueryResult<T extends GraphQueryItem> = {
  all: T[];
  focus: T[];
};

export const parseOpSelectionQuery = <T extends GraphQueryItem>(
  all_ops: T[],
  query: string,
): OpSelectionQueryResult<T> | Error => {
  try {
    const lexer = new OpSelectionLexer(CharStreams.fromString(query));
    lexer.removeErrorListeners();
    lexer.addErrorListener(new AntlrInputErrorListener());

    const tokenStream = new CommonTokenStream(lexer);

    const parser = new OpSelectionParser(tokenStream);
    parser.removeErrorListeners();
    parser.addErrorListener(new AntlrInputErrorListener());

    const tree = parser.start();

    const visitor = new AntlrOpSelectionVisitor(all_ops);
    const all_selection = visitor.visit(tree);
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
  if (featureEnabled(FeatureFlag.flagSelectionSyntax)) {
    const result = parseOpSelectionQuery(all_ops, query);
    if (result instanceof Error) {
      // fall back to old behavior
      return filterByQuery(all_ops, query);
    }
    return result;
  }
  return filterByQuery(all_ops, query);
};
