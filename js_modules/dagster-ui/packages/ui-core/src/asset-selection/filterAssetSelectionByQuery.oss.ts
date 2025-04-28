import {FeatureFlag} from 'shared/app/FeatureFlags.oss';

import {AssetSelectionQueryResult, parseAssetSelectionQuery} from './parseAssetSelectionQuery';
import {SupplementaryInformation} from './types';
import {featureEnabled} from '../app/Flags';
import {filterByQuery} from '../app/GraphQueryImpl';
import {AssetGraphQueryItem} from '../asset-graph/types';
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
