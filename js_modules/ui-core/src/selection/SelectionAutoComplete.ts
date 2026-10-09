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
  supportsNot = true,
}: Omit<SelectionAutoCompleteProvider, 'renderResult' | 'useAutoComplete'>) {
  return function (line: string, actualCursorIndex: number) {
    const {parseTrees} = parseInput(line);
    const treeAtCursor = parseTrees.find(
      ({startOffset, line: treeLine}) =>
        actualCursorIndex >= startOffset && actualCursorIndex - startOffset <= treeLine.length,
    );
    const isInLeadingWhitespace = actualCursorIndex < (parseTrees[0]?.startOffset ?? 0);
    const start = treeAtCursor?.startOffset ?? 0;

    let visitorWithAutoComplete;
    if (!parseTrees.length || isInLeadingWhitespace) {
      // An empty input, or the cursor in its leading whitespace, gets unmatched value results
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
        supportsNot,
      });
      visitorWithAutoComplete.addUnmatchedValueResults('');
    } else if (treeAtCursor) {
      visitorWithAutoComplete = new SelectionAutoCompleteVisitor({
        line: treeAtCursor.line,
        cursorIndex: actualCursorIndex - start,
        getAttributeResultsMatchingQuery,
        getAttributeValueResultsMatchingQuery,
        getAllResults,
        getFunctionResultsMatchingQuery,
        getSubstringResultMatchingQuery,
        createOperatorSuggestion,
        supportsTraversal,
        supportsNot,
      });
      treeAtCursor.tree.accept(visitorWithAutoComplete);
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
