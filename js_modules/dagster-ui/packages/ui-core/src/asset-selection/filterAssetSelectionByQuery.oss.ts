import {FeatureFlag} from 'shared/app/FeatureFlags.oss';
import {SupplementaryInformation} from 'shared/asset-graph/useAssetGraphSupplementaryData.oss';

import {AssetSelectionQueryResult, parseAssetSelectionQuery} from './parseAssetSelectionQuery';
import {featureEnabled} from '../app/Flags';
import {filterByQuery} from '../app/GraphQueryImpl';
import {AssetGraphQueryItem} from '../asset-graph/useAssetGraphData';
import {weakMapMemoize} from '../util/weakMapMemoize';

export const filterAssetSelectionByQuery = weakMapMemoize(
  (
    all_assets: AssetGraphQueryItem[],
    query: string,
    supplementaryData: SupplementaryInformation,
  ): AssetSelectionQueryResult => {
    if (query.length === 0) {
      return {all: all_assets, focus: []};
    }
    if (featureEnabled(FeatureFlag.flagSelectionSyntax)) {
      const result = parseAssetSelectionQuery(all_assets, query, supplementaryData);
      if (result instanceof Error) {
        return {all: [], focus: []};
      }
      return result;
    }
    return filterByQuery(all_assets, query);
  },
  {maxEntries: 20},
);
