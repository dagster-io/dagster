import {parseRunsSearch} from './parseRunsSearch';
import {RUNS_SEARCH_ATTRIBUTES} from './runsSearchAttributes';
import {SyntaxError} from '../../selection/CustomErrorListener';
import {createSelectionLinter} from '../../selection/createSelectionLinter';
import {SelectionAutoCompleteLexer} from '../../selection/generated/SelectionAutoCompleteLexer';
import {SelectionAutoCompleteParser} from '../../selection/generated/SelectionAutoCompleteParser';
import {weakMapMemoize} from '../../util/weakMapMemoize';

const lintSyntax = createSelectionLinter({
  Lexer: SelectionAutoCompleteLexer,
  Parser: SelectionAutoCompleteParser,
  supportedAttributes: RUNS_SEARCH_ATTRIBUTES,
});

export const lintRunsSearch = weakMapMemoize(
  (text: string): SyntaxError[] => {
    // Blank text clears the search, but the grammar requires an expression.
    if (text.trim() === '') {
      return [];
    }

    const syntaxErrors = lintSyntax(text);
    if (!syntaxErrors.length) {
      return parseRunsSearch(text).errors;
    }
    return syntaxErrors;
  },
  {maxEntries: 20},
);
