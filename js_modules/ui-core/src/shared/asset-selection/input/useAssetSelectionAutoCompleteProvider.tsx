import {useMemo} from 'react';

import {AssetGraphQueryItem} from '../../../asset-graph/types';
import {useAutomationNames} from '../../../asset-selection/input/useAutomationNames';
import {attributeToIcon, getAttributesMap} from '../../../asset-selection/input/util';
import {createSelectionAutoComplete} from '../../../selection/SelectionAutoComplete';
import {
  SelectionAutoCompleteProvider,
  createProvider,
} from '../../../selection/SelectionAutoCompleteProvider';

export function useAssetSelectionAutoCompleteProvider(
  assets: AssetGraphQueryItem[],
): Pick<SelectionAutoCompleteProvider, 'useAutoComplete'> {
  const {sensorNames, scheduleNames} = useAutomationNames();

  const attributesMap = useMemo(
    () => getAttributesMap(assets, {sensorNames, scheduleNames}),
    [assets, sensorNames, scheduleNames],
  );

  const baseProvider = useMemo(
    () =>
      createProvider({
        attributesMap,
        primaryAttributeKey: 'key',
        attributeToIcon,
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
