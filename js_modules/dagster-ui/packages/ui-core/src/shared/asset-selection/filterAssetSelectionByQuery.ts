import {AssetGraphQueryItem} from '../../asset-graph/types';
import {
  AssetSelectionQueryResult,
  parseAssetSelectionQuery,
} from '../../asset-selection/parseAssetSelectionQuery';
import {SupplementaryInformation} from '../../asset-selection/types';
import {weakMapMemoize} from '../../util/weakMapMemoize';

export const filterAssetSelectionByQuery = weakMapMemoize(
  (
    all_assets: AssetGraphQueryItem[],
    query: string,
    supplementaryData: SupplementaryInformation,
  ): AssetSelectionQueryResult => {
    if (query.length === 0) {
      return {all: all_assets, focus: []};
    }
    const result = parseAssetSelectionQuery(all_assets, query, supplementaryData);
    if (result instanceof Error) {
      return {all: [], focus: []};
    }
    return result;
  },
  {maxEntries: 10},
);
