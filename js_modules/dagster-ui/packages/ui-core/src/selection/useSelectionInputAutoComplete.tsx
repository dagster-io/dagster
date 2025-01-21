import {useMemo} from 'react';

import {generateAutocompleteResults} from './SelectionAutoComplete';

export function useSelectionInputAutoComplete<
  T extends Record<string, string[]>,
  N extends keyof T,
>({
  value,
  cursor,
  nameBase,
  attributesMap,
  functions,
}: {
  value: string;
  cursor: number;
  nameBase: N;
  attributesMap: T;
  functions: string[];
}) {
  const hintFn = useMemo(() => {
    return generateAutocompleteResults({nameBase, attributesMap, functions});
  }, [nameBase, attributesMap, functions]);

  const autocompleteResults = useMemo(() => {
    return hintFn(value, cursor);
  }, [hintFn, value, cursor]);

  return autocompleteResults;
}
