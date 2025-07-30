import {SelectionAutoCompleteProvider} from './SelectionAutoCompleteProvider';
import {SelectionAutoCompleteVisitor} from './SelectionAutoCompleteVisitor';
import {parseInput} from './SelectionInputParser';

export function createSelectionAutoComplete({
  getAttributeResultsMatchingQuery,
  getAttributeValueResultsMatchingQuery,
  getFunctionResultsMatchingQuery,
  getSubstringResultMatchingQuery,
  getAllResults,
  createOperatorSuggestion,
  supportsTraversal = true,
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
        getAllResults,
        getFunctionResultsMatchingQuery,
        getSubstringResultMatchingQuery,
        createOperatorSuggestion,
        supportsTraversal,
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
            getAllResults,
            getFunctionResultsMatchingQuery,
            getSubstringResultMatchingQuery,
            createOperatorSuggestion,
            supportsTraversal,
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
