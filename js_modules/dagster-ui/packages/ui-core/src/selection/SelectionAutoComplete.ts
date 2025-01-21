import {SelectionAutoCompleteVisitor} from './SelectionAutoCompleteVisitor';
import {parseInput} from './SelectionInputParser';

export function generateAutocompleteResults<T extends Record<string, string[]>, N extends keyof T>({
  nameBase: _nameBase,
  attributesMap,
  functions,
}: {
  nameBase: N;
  attributesMap: T;
  functions: string[];
}) {
  const nameBase = _nameBase as string;

  return function (line: string, actualCursorIndex: number) {
    const {parseTrees} = parseInput(line);

    let start = 0;

    let visitorWithAutoComplete;
    if (!parseTrees.length) {
      // Special case empty string to add unmatched value results
      visitorWithAutoComplete = new SelectionAutoCompleteVisitor({
        attributesMap,
        functions,
        nameBase,
        line,
        cursorIndex: actualCursorIndex,
      });
      start = actualCursorIndex;
      visitorWithAutoComplete.addUnmatchedValueResults('');
    } else {
      for (const {tree, line} of parseTrees) {
        const cursorIndex = actualCursorIndex - start;
        const visitor = new SelectionAutoCompleteVisitor({
          attributesMap,
          functions,
          nameBase,
          line,
          cursorIndex,
        });
        visitor.visit(tree);
        const length = line.length;
        if (cursorIndex <= length) {
          visitorWithAutoComplete = visitor;
          break;
        }
        start += length;
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
