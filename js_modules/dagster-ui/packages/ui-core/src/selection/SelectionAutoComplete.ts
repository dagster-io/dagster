import {SelectionAutoCompleteProvider} from './SelectionAutoCompleteProvider';
import {SelectionAutoCompleteVisitor} from './SelectionAutoCompleteVisitor';
import {parseInput} from './SelectionInputParser';

export function createSelectionAutoComplete({
  getAttributeResultsMatchingQuery,
  getAttributeValueResultsMatchingQuery,
  getFunctionResultsMatchingQuery,
  getSubstringResultMatchingQuery,
  getAttributeValueIncludeAttributeResultsMatchingQuery,
  createOperatorSuggestion,
}: Omit<SelectionAutoCompleteProvider, 'renderResult' | 'useAutoComplete'>) {
  return function (line: string, actualCursorIndex: number) {
    const {parseTrees} = parseInput(line);

    let start = 0;

    let visitorWithAutoComplete;
    if (!parseTrees.length) {
      // Special case empty string to add unmatched value results
      visitorWithAutoComplete = new SelectionAutoCompleteVisitor({
        line,
        cursorIndex: actualCursorIndex,
        getAttributeResultsMatchingQuery,
        getAttributeValueResultsMatchingQuery,
        getAttributeValueIncludeAttributeResultsMatchingQuery,
        getFunctionResultsMatchingQuery,
        getSubstringResultMatchingQuery,
        createOperatorSuggestion,
      });
      visitorWithAutoComplete.addUnmatchedValueResults('');
    } else {
      for (const {tree, line} of parseTrees) {
        const cursorIndex = actualCursorIndex - start;

        if (cursorIndex <= line.length) {
          const visitor = new SelectionAutoCompleteVisitor({
            line,
            cursorIndex,
            getAttributeResultsMatchingQuery,
            getAttributeValueResultsMatchingQuery,
            getAttributeValueIncludeAttributeResultsMatchingQuery,
            getFunctionResultsMatchingQuery,
            getSubstringResultMatchingQuery,
            createOperatorSuggestion,
          });
          tree.accept(visitor);
          visitorWithAutoComplete = visitor;
          break;
        }
        start += line.length;
      }
    }
    if (visitorWithAutoComplete) {
      return {
        list: visitorWithAutoComplete.list,
        from: start + visitorWithAutoComplete.startReplacementIndex,
        to: start + visitorWithAutoComplete.stopReplacementIndex,
      };
    }
    return {list: [], from: 0, to: 0};
  };
}
