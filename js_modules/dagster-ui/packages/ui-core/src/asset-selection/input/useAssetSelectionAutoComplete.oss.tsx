import {useMemo} from 'react';

import {getAttributesMap} from './util';
import {AssetGraphQueryItem} from '../../asset-graph/useAssetGraphData';
import {useSelectionInputAutoComplete} from '../../selection/useSelectionInputAutoComplete';

const FUNCTIONS = ['sinks', 'roots'];

export function createUseAssetSelectionAutoComplete(assets: AssetGraphQueryItem[]) {
  return function useAssetSelectionAutoComplete(value: string, cursor: number) {
    const attributesMap = useMemo(() => getAttributesMap(assets), []);
    return {
      autoCompleteResults: useSelectionInputAutoComplete({
        nameBase: 'key',
        attributesMap,
        functions: FUNCTIONS,
        value,
        cursor,
      }),
      loading: false,
    };
  };
}
