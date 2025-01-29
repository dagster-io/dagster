import {IconName} from '@dagster-io/ui-components';
import {useMemo} from 'react';

import {getAttributesMap} from './util';
import {AssetGraphQueryItem} from '../../asset-graph/useAssetGraphData';
import {createSelectionAutoComplete} from '../../selection/SelectionAutoComplete';
import {
  SelectionAutoCompleteProvider,
  createProvider,
} from '../../selection/SelectionAutoCompleteProvider';
import {createAttributeBasedAutoCompleteProvider} from '../../selection/SelectionAutoCompleteProviderFromAttributeMap';

type Attribute = 'kind' | 'code_location' | 'group' | 'owner' | 'tag' | 'status' | 'key';

export function useAssetSelectionAutoCompleteProvider(
  assets: AssetGraphQueryItem[],
): SelectionAutoCompleteProvider {
  const attributesMap = useMemo(() => getAttributesMap(assets), [assets]);

  const baseProvider = useMemo(
    () =>
      createAttributeBasedAutoCompleteProvider({
        attributesMap,
        ...createProvider<typeof attributesMap, 'key'>({
          primaryAttributeKey: 'key',
          attributeToIcon: iconMap,
        }),
      }),
    [attributesMap],
  );
  const selectionHint = useMemo(() => createSelectionAutoComplete(baseProvider), [baseProvider]);

  return {
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
  };
}

export const iconMap: Record<Attribute, IconName> = {
  key: 'magnify_glass',
  kind: 'compute_kind',
  code_location: 'code_location',
  group: 'asset_group',
  owner: 'owner',
  tag: 'tag',
  status: 'status',
};
