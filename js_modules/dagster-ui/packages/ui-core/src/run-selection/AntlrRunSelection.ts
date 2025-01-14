import {CharStreams, CommonTokenStream} from 'antlr4ts';
import {FeatureFlag} from 'shared/app/FeatureFlags.oss';

import {AntlrRunSelectionVisitor} from './AntlrRunSelectionVisitor';
import {AntlrInputErrorListener} from '../asset-selection/AntlrAssetSelection';
import {RunGraphQueryItem} from '../gantt/toGraphQueryItems';
import {RunSelectionLexer} from './generated/RunSelectionLexer';
import {RunSelectionParser} from './generated/RunSelectionParser';
import {featureEnabled} from '../app/Flags';
import {filterByQuery} from '../app/GraphQueryImpl';
import {weakMapMemoize} from '../util/weakMapMemoize';

export type RunSelectionQueryResult = {
  all: RunGraphQueryItem[];
  focus: RunGraphQueryItem[];
};

export const parseRunSelectionQuery = (
  all_runs: RunGraphQueryItem[],
  query: string,
): RunSelectionQueryResult | Error => {
  try {
    const lexer = new RunSelectionLexer(CharStreams.fromString(query));
    lexer.removeErrorListeners();
    lexer.addErrorListener(new AntlrInputErrorListener());

    const tokenStream = new CommonTokenStream(lexer);

    const parser = new RunSelectionParser(tokenStream);
    parser.removeErrorListeners();
    parser.addErrorListener(new AntlrInputErrorListener());

    const tree = parser.start();

    const visitor = new AntlrRunSelectionVisitor(all_runs);
    const all_selection = visitor.visit(tree);
    const focus_selection = visitor.focus_runs;

    return {
      all: Array.from(all_selection),
      focus: Array.from(focus_selection),
    };
  } catch (e) {
    return e as Error;
  }
};

export const filterRunSelectionByQuery = weakMapMemoize(
  (all_runs: RunGraphQueryItem[], query: string): RunSelectionQueryResult => {
    if (featureEnabled(FeatureFlag.flagSelectionSyntax)) {
      const result = parseRunSelectionQuery(all_runs, query);
      if (result instanceof Error) {
        // fall back to old behavior
        return filterByQuery(all_runs, query);
      }
      return result;
    }
    return filterByQuery(all_runs, query);
  },
  {maxEntries: 20},
);
