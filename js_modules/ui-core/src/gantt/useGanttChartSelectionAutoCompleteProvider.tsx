import {useMemo} from 'react';

import {RunGraphQueryItem} from './toGraphQueryItems';
import {NO_STATE} from '../run-selection/AntlrRunSelectionVisitor';
import {createSelectionAutoComplete} from '../selection/SelectionAutoComplete';
import {
  SelectionAutoCompleteProvider,
  createProvider,
} from '../selection/SelectionAutoCompleteProvider';

export const ganttChartSelectionSyntaxSupportedAttributes = ['name', 'status'] as const;

export function useGanttChartSelectionAutoCompleteProvider(
  items: RunGraphQueryItem[],
): Pick<SelectionAutoCompleteProvider, 'useAutoComplete'> {
  const attributesMap = useMemo(() => {
    const statuses = new Set<string>();
    const names = new Set<string>();

    items.forEach((item) => {
      if (item.metadata?.state) {
        statuses.add(item.metadata.state);
      } else {
        statuses.add(NO_STATE);
      }
      names.add(item.name);
    });
    return {name: Array.from(names), status: Array.from(statuses)};
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

  return {
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
  };
}

export const iconMap = {
  name: 'magnify_glass',
  status: 'status',
} as const;
