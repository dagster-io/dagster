import {CharStreams, CommonTokenStream} from 'antlr4ts';

import {AntlrOpSelectionVisitor} from './AntlrOpSelectionVisitor';
import {GraphQueryItem} from '../app/GraphQueryImpl';
import {AntlrInputErrorListener} from '../asset-selection/AntlrAssetSelection';
import {OpSelectionLexer} from './generated/OpSelectionLexer';
import {OpSelectionParser} from './generated/OpSelectionParser';

type OpSelectionQueryResult = {
  all: GraphQueryItem[];
  focus: GraphQueryItem[];
};

export const parseOpSelectionQuery = (
  all_ops: GraphQueryItem[],
  query: string,
): OpSelectionQueryResult | Error => {
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
