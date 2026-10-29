import {useMemo} from 'react';

import {GraphQueryItem} from '../app/GraphQueryImpl';
import {iconMap} from '../gantt/useGanttChartSelectionAutoCompleteProvider';
import {
  createSelectionAutoComplete,
  useSelectionAutoCompleteResults,
} from '../selection/SelectionAutoComplete';
import {
  SelectionAutoCompleteProvider,
  createProvider,
} from '../selection/SelectionAutoCompleteProvider';

export const opGraphSelectionSyntaxSupportedAttributes = ['name'] as const;

export const useOpGraphSelectionAutoCompleteProvider = (
  items: GraphQueryItem[],
): Pick<SelectionAutoCompleteProvider, 'useAutoComplete'> => {
  const attributesMap = useMemo(() => {
    const names = new Set<string>();
    items.forEach((item) => {
      names.add(item.name);
    });
    return {name: Array.from(names)};
  }, [items]);

  const baseProvider = useMemo(
    () =>
      createProvider({
        attributesMap,
        primaryAttributeKey: 'name',
        attributeToIcon: iconMap,
      }),
    [attributesMap],
  );
  const selectionHint = useMemo(() => createSelectionAutoComplete(baseProvider), [baseProvider]);

  return useMemo(
    () => ({
      useAutoComplete: ({line, cursorIndex}) => {
        const autoCompleteResults = useSelectionAutoCompleteResults(
          selectionHint,
          line,
          cursorIndex,
        );
        return {
          autoCompleteResults,
          loading: false,
        };
      },
    }),
    [selectionHint],
  );
};
