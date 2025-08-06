import {CharStreams, CommonTokenStream} from 'antlr4ts';

import {AntlrAutomationSelectionVisitor} from './AntlrAutomationSelectionVisitor';
import {AutomationSelectionLexer} from './generated/AutomationSelectionLexer';
import {AutomationSelectionParser} from './generated/AutomationSelectionParser';
import {AntlrInputErrorListener} from '../asset-selection/parseAssetSelectionQuery';
import {Automation} from './input/useAutomationSelectionAutoCompleteProvider';

export const parseAutomationSelectionQuery = <T extends Automation>(
  all_automations: T[],
  query: string,
): Set<T> | Error => {
  try {
    const lexer = new AutomationSelectionLexer(CharStreams.fromString(query));
    lexer.removeErrorListeners();
    lexer.addErrorListener(new AntlrInputErrorListener());

    const tokenStream = new CommonTokenStream(lexer);

    const parser = new AutomationSelectionParser(tokenStream);
    parser.removeErrorListeners();
    parser.addErrorListener(new AntlrInputErrorListener());

    const tree = parser.start();

    const visitor = new AntlrAutomationSelectionVisitor(all_automations);
    return visitor.visit(tree);
  } catch (e) {
    return e as Error;
  }
};

export const filterAutomationSelectionByQuery = <T extends Automation>(
  all_automations: T[],
  query: string,
): Set<T> => {
  if (query.length === 0) {
    return new Set(all_automations);
  }
  const result = parseAutomationSelectionQuery(all_automations, query);
  if (result instanceof Error) {
    return new Set();
  }
  return result;
};
