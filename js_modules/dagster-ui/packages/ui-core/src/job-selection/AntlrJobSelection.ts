import {CharStream, CommonTokenStream} from 'antlr4ng';

import {AntlrJobSelectionVisitor} from './AntlrJobSelectionVisitor';
import {JobSelectionLexer} from './generated/JobSelectionLexer';
import {JobSelectionParser} from './generated/JobSelectionParser';
import {AntlrInputErrorListener} from '../asset-selection/parseAssetSelectionQuery';
import {RepoAddress} from '../workspace/types';

type JobSelectionQueryResult<T> = {
  all: Set<T>;
};

export type Job = {
  name: string;
  repo: RepoAddress;
};

export const parseJobSelectionQuery = <T extends Job>(
  all_jobs: T[],
  query: string,
): JobSelectionQueryResult<T> | Error => {
  try {
    const lexer = new JobSelectionLexer(CharStream.fromString(query));
    lexer.removeErrorListeners();
    lexer.addErrorListener(new AntlrInputErrorListener());

    const tokenStream = new CommonTokenStream(lexer);

    const parser = new JobSelectionParser(tokenStream);
    parser.removeErrorListeners();
    parser.addErrorListener(new AntlrInputErrorListener());

    const tree = parser.start();

    const visitor = new AntlrJobSelectionVisitor(all_jobs);
    const all_selection = visitor.visit(tree) ?? new Set<T>();

    return {
      all: all_selection,
    };
  } catch (e) {
    return e as Error;
  }
};

export const filterJobSelectionByQuery = <T extends Job>(
  all_jobs: T[],
  query: string,
): JobSelectionQueryResult<T> => {
  if (query.length === 0) {
    return {all: new Set(all_jobs)};
  }
  const result = parseJobSelectionQuery(all_jobs, query);
  if (result instanceof Error || !result.all) {
    return {all: new Set()};
  }
  return result;
};
