import {useMemo} from 'react';

import {GraphQueryItem} from '../app/GraphQueryImpl';
import {iconMap} from '../gantt/useGanttChartSelectionAutoCompleteProvider';
import {createSelectionAutoComplete} from '../selection/SelectionAutoComplete';
import {
  SelectionAutoCompleteProvider,
  createProvider,
} from '../selection/SelectionAutoCompleteProvider';
import {createSelectionAutoCompleteProviderFromAttributeMap} from '../selection/SelectionAutoCompleteProviderFromAttributeMap';

export const useOpGraphSelectionAutoCompleteProvider = (
  items: GraphQueryItem[],
): SelectionAutoCompleteProvider => {
  const attributesMap = useMemo(() => {
    const names = new Set<string>();
    items.forEach((item) => {
      names.add(item.name);
    });
    return {name: Array.from(names)};
  }, [items]);

  const baseProvider = useMemo(
    () =>
      createSelectionAutoCompleteProviderFromAttributeMap({
        attributesMap,
        ...createProvider<typeof attributesMap, 'name'>({
          nameBase: 'name',
          attributeToIcon: iconMap,
        }),
      }),
    [attributesMap],
  );
  const selectionHint = useMemo(() => createSelectionAutoComplete(baseProvider), [baseProvider]);

  return useMemo(
    () => ({
      ...baseProvider,
      useAutoComplete: ({line, cursorIndex}) => {
        const autoCompleteResults = useMemo(
          () => selectionHint(line, cursorIndex),
          [line, cursorIndex],
        );
        return {
          autoCompleteResults,
          loading: false,
        };
      },
    }),
    [baseProvider, selectionHint],
  );
};
