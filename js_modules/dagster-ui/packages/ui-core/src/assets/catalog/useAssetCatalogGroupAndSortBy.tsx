import {ParsedQs} from 'qs';
import {useCallback, useMemo} from 'react';

import {Grouped} from './AssetCatalogV2VirtualizedTable';
import {AssetHealthGroupBy, AttributeStatusHeaderRow, GROUP_BY} from './AttributeStatusHeaderRow';
import {HealthStatusHeaderRow} from './HealthStatusHeaderRow';
import {COMMON_COLLATOR, assertUnreachable} from '../../app/Util';
import {usePrefixedCacheKey} from '../../app/usePrefixedCacheKey';
import {AssetHealthFragment} from '../../asset-data/types/AssetHealthDataProvider.types';
import {tokenForAssetKey} from '../../asset-graph/Utils';
import {AssetHealthStatus} from '../../graphql/types';
import {useQueryAndLocalStoragePersistedState} from '../../hooks/useQueryAndLocalStoragePersistedState';
import {weakMapMemoize} from '../../util/weakMapMemoize';
import {buildRepoPathForHuman} from '../../workspace/buildRepoAddress';
import {statusToIconAndColor} from '../AssetHealthSummary';
import {AssetTableFragment} from '../types/AssetTableFragment.types';

const SORT_ITEMS = [
  {
    key: 'materialization_asc' as const,
    text: 'Materialization (new to old)',
  },
  {
    key: 'materialization_desc' as const,
    text: 'Materialization (old to new)',
  },
  {
    key: 'key_asc' as const,
    text: 'Asset key (a to z)',
  },
  {
    key: 'key_desc' as const,
    text: 'Asset key (z to a)',
  },
];

const ITEMS_BY_KEY = SORT_ITEMS.reduce(
  (acc, item) => {
    acc[item.key] = item;
    return acc;
  },
  {} as Record<(typeof SORT_ITEMS)[number]['key'], (typeof SORT_ITEMS)[number]>,
);

type UseAssetCatalogGroupAndSortByProps = {
  liveDataByNode: Record<string, AssetHealthFragment>;
  assetsByAssetKey: Map<string, AssetTableFragment>;
};

type SortBy = (typeof SORT_ITEMS)[number]['key'];

export const useAssetCatalogGroupAndSortBy = ({
  liveDataByNode,
  assetsByAssetKey,
}: UseAssetCatalogGroupAndSortByProps) => {
  const [sortBy, setSortBy] = useQueryAndLocalStoragePersistedState<SortBy>({
    localStorageKey: usePrefixedCacheKey('catalog-sortBy'),
    isEmptyState: (state) => !state || state === 'materialization_asc',
    decode: useCallback((json: ParsedQs) => {
      if (
        ['materialization_asc', 'materialization_desc', 'key_asc', 'key_desc'].includes(
          json.sortBy as SortBy,
        )
      ) {
        return json.sortBy as SortBy;
      }
      return 'materialization_asc';
    }, []),
    encode: useCallback((sortBy: SortBy) => ({sortBy}), []),
  });

  const [groupBy, setGroupBy] = useQueryAndLocalStoragePersistedState<AssetHealthGroupBy>({
    localStorageKey: usePrefixedCacheKey('catalog-groupBy'),
    isEmptyState: (state) => !state || state === AssetHealthGroupBy.health_status,
    decode: useCallback((qs: ParsedQs) => {
      if (qs.groupBy && GROUP_BY.includes(qs.groupBy as AssetHealthGroupBy)) {
        return qs.groupBy as AssetHealthGroupBy;
      }
      return AssetHealthGroupBy.health_status;
    }, []),
    encode: useCallback((b: AssetHealthGroupBy) => ({groupBy: b}), []),
  });

  const grouped: Record<string, Grouped<any>> = useMemo(() => {
    switch (groupBy) {
      case AssetHealthGroupBy.code_location:
        return groupByAttribute({
          liveDataByNode,
          getAttributes: ({key}) => {
            const asset = assetsByAssetKey.get(tokenForAssetKey(key));
            const repo = asset?.definition?.repository;
            return [repo ? buildRepoPathForHuman(repo.name, repo.location.name) : 'None'];
          },
          renderGroupHeader: (props) => {
            return (
              <AttributeStatusHeaderRow
                {...props}
                text={props.group}
                groupBy={AssetHealthGroupBy.code_location}
              />
            );
          },
        });
      case AssetHealthGroupBy.group:
        return groupByAttribute({
          liveDataByNode,
          getAttributes: ({key}) => {
            const asset = assetsByAssetKey.get(tokenForAssetKey(key));
            return [asset?.definition?.groupName ?? 'default'];
          },
          renderGroupHeader: (props) => {
            return (
              <AttributeStatusHeaderRow
                {...props}
                text={props.group}
                groupBy={AssetHealthGroupBy.group}
              />
            );
          },
        });
      case AssetHealthGroupBy.owner:
        return groupByAttribute({
          liveDataByNode,
          getAttributes: ({key}) => {
            const asset = assetsByAssetKey.get(tokenForAssetKey(key));
            return (
              asset?.definition?.owners.map((owner) =>
                'email' in owner ? owner.email : owner.team,
              ) ?? ['None']
            );
          },
          renderGroupHeader: (props) => {
            return (
              <AttributeStatusHeaderRow
                {...props}
                text={props.group}
                groupBy={AssetHealthGroupBy.owner}
              />
            );
          },
        });
      case AssetHealthGroupBy.kind:
        return groupByAttribute({
          liveDataByNode,
          getAttributes: ({key}) => {
            const asset = assetsByAssetKey.get(tokenForAssetKey(key));
            if (asset?.definition?.computeKind || asset?.definition?.kinds?.length) {
              return Array.from(
                new Set(
                  [asset?.definition?.computeKind, ...(asset?.definition?.kinds ?? [])].filter(
                    Boolean,
                  ) as string[],
                ),
              );
            }
            return [];
          },
          renderGroupHeader: (props) => {
            return (
              <AttributeStatusHeaderRow
                {...props}
                text={props.group}
                groupBy={AssetHealthGroupBy.kind}
              />
            );
          },
        });
      case AssetHealthGroupBy.tags:
        return groupByAttribute({
          liveDataByNode,
          getAttributes: ({key}) => {
            const asset = assetsByAssetKey.get(tokenForAssetKey(key));
            return asset?.definition?.tags.map((tag) => `${tag.key}: ${tag.value}`) ?? [];
          },
          renderGroupHeader: (props) => {
            return (
              <AttributeStatusHeaderRow
                {...props}
                text={props.group}
                groupBy={AssetHealthGroupBy.tags}
              />
            );
          },
        });
      case AssetHealthGroupBy.materialization_status:
        return groupByAttribute({
          liveDataByNode,
          getAttributes: (asset) => {
            return [
              statusToIconAndColor[asset.assetHealth?.freshnessStatus ?? AssetHealthStatus.UNKNOWN]
                .text,
            ];
          },
          renderGroupHeader: (props) => {
            return <HealthStatusHeaderRow {...props} status={props.group} groupBy={groupBy} />;
          },
        });
      case AssetHealthGroupBy.freshness_status:
        return groupByAttribute({
          liveDataByNode,
          getAttributes: (asset) => {
            return [
              statusToIconAndColor[asset.assetHealth?.freshnessStatus ?? AssetHealthStatus.UNKNOWN]
                .text,
            ];
          },
          renderGroupHeader: (props) => {
            return <HealthStatusHeaderRow {...props} status={props.group} groupBy={groupBy} />;
          },
        });
      case AssetHealthGroupBy.check_status:
        return groupByAttribute({
          liveDataByNode,
          getAttributes: (asset) => {
            return [
              statusToIconAndColor[
                asset.assetHealth?.assetChecksStatus ?? AssetHealthStatus.UNKNOWN
              ].text,
            ];
          },
          renderGroupHeader: (props) => {
            return <HealthStatusHeaderRow {...props} status={props.group} groupBy={groupBy} />;
          },
        });
      case AssetHealthGroupBy.health_status:
      default:
        return groupByAttribute({
          liveDataByNode,
          getAttributes: (asset) => {
            return [
              statusToIconAndColor[asset.assetHealth?.assetHealth ?? AssetHealthStatus.UNKNOWN]
                .text,
            ];
          },
          renderGroupHeader: (props) => {
            return <HealthStatusHeaderRow {...props} status={props.group} groupBy={groupBy} />;
          },
        });
    }
  }, [assetsByAssetKey, groupBy, liveDataByNode]);

  const allGroups = useMemo(() => {
    switch (groupBy) {
      case AssetHealthGroupBy.health_status:
      case AssetHealthGroupBy.freshness_status:
      case AssetHealthGroupBy.check_status:
        return ['Degraded', 'Warning', 'Healthy', 'Unknown'];

      default:
        return Object.keys(grouped).sort((a, b) => COMMON_COLLATOR.compare(a, b));
    }
  }, [groupBy, grouped]);

  const groupedAndSorted = useMemo(() => {
    let sortFn;
    switch (sortBy) {
      case 'materialization_asc':
        sortFn = (a: AssetHealthFragment, b: AssetHealthFragment) =>
          sortAssetsByMaterializationTimestamp(a, b);
        break;
      case 'materialization_desc':
        sortFn = (a: AssetHealthFragment, b: AssetHealthFragment) =>
          sortAssetsByMaterializationTimestamp(b, a);
        break;
      case 'key_asc':
        sortFn = (a: AssetHealthFragment, b: AssetHealthFragment) =>
          COMMON_COLLATOR.compare(tokenForAssetKey(a.key), tokenForAssetKey(b.key));
        break;
      case 'key_desc':
        sortFn = (a: AssetHealthFragment, b: AssetHealthFragment) =>
          COMMON_COLLATOR.compare(tokenForAssetKey(b.key), tokenForAssetKey(a.key));
        break;
      default:
        assertUnreachable(sortBy);
    }
    const copy = {...grouped};
    Object.entries(copy).forEach(([group, groupData]) => {
      copy[group] = {
        ...groupData,
        assets: groupData.assets.slice().sort(sortFn),
      };
    });
    return copy;
  }, [grouped, sortBy]);

  return {
    sortBy,
    setSortBy,
    groupBy,
    setGroupBy,
    grouped,
    groupedAndSorted,
    allGroups,
    SORT_ITEMS,
    ITEMS_BY_KEY,
  };
};

function sortAssetsByMaterializationTimestamp(a: AssetHealthFragment, b: AssetHealthFragment) {
  const aMaterialization = a.assetMaterializations[0]?.timestamp;
  const bMaterialization = b.assetMaterializations[0]?.timestamp;
  if (!aMaterialization && !bMaterialization) {
    return 0;
  }
  if (!aMaterialization) {
    return 1;
  }
  if (!bMaterialization) {
    return -1;
  }
  return Number(bMaterialization) - Number(aMaterialization);
}

const groupByAttribute = weakMapMemoize(
  <T extends string>({
    liveDataByNode,
    getAttributes,
    renderGroupHeader,
  }: {
    liveDataByNode: Record<string, AssetHealthFragment>;
    getAttributes: (asset: AssetHealthFragment) => T[];
    renderGroupHeader: Grouped<T>['renderGroupHeader'];
  }): Record<T, Grouped<T>> => {
    const byAttribute: {[key in T]: Grouped<T>} = {} as {[key in T]: Grouped<T>};
    Object.values(liveDataByNode).forEach((asset) => {
      const attributes = getAttributes(asset);
      attributes.forEach((attribute) => {
        if (!byAttribute[attribute]) {
          byAttribute[attribute] = {
            assets: [],
            renderGroupHeader,
          };
        }
        byAttribute[attribute].assets.push(asset);
      });
    });
    return byAttribute;
  },
);

export function isHealthGroupBy(groupBy: AssetHealthGroupBy) {
  return [
    AssetHealthGroupBy.health_status,
    AssetHealthGroupBy.freshness_status,
    AssetHealthGroupBy.check_status,
    AssetHealthGroupBy.materialization_status,
  ].includes(groupBy);
}
