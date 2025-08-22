import {
  Body,
  Box,
  Colors,
  Icon,
  MenuItem,
  NonIdealState,
  Popover,
  Select,
  Skeleton,
  Subtitle1,
  Tab,
  Tabs,
  Tag,
  UnstyledButton,
  ifPlural,
} from '@dagster-io/ui-components';
import {ParsedQs} from 'qs';
import React, {useCallback, useEffect, useMemo, useState} from 'react';
import {useRouteMatch} from 'react-router-dom';
import {useSetRecoilState} from 'recoil';
import {CreateCatalogViewButton} from 'shared/assets/CreateCatalogViewButton.oss';
import {
  AssetCatalogAlerts,
  useShouldShowAssetCatalogAlerts,
} from 'shared/assets/catalog/AssetCatalogAlerts.oss';
import {useCatalogExtraDropdownOptions} from 'shared/assets/catalog/useCatalogExtraDropdownOptions.oss';
import {AssetCatalogInsights} from 'shared/assets/insights/AssetCatalogInsights.oss';
import {useFavoriteAssets} from 'shared/assets/useFavoriteAssets.oss';

import {AssetCatalogAssetGraph} from './AssetCatalogAssetGraph';
import {
  AssetCatalogV2VirtualizedTable,
  AssetCatalogV2VirtualizedTableProps,
  Grouped,
} from './AssetCatalogV2VirtualizedTable';
import {
  AssetHealthGroupBy,
  AttributeStatusHeaderRow,
  GROUP_BY,
  GROUP_BY_ITEMS,
} from './AttributeStatusHeaderRow';
import {HealthStatusHeaderRow} from './HealthStatusHeaderRow';
import {SelectedAssetsPopoverContent} from './SelectedAssetsPopoverContent';
import {useFullScreen} from '../../app/AppTopNav/AppTopNavContext';
import {PythonErrorInfo} from '../../app/PythonErrorInfo';
import {COMMON_COLLATOR, assertUnreachable} from '../../app/Util';
import {currentPageAtom, useTrackEvent} from '../../app/analytics';
import {usePrefixedCacheKey} from '../../app/usePrefixedCacheKey';
import {useAssetsHealthData} from '../../asset-data/AssetHealthDataProvider';
import {AssetHealthFragment} from '../../asset-data/types/AssetHealthDataProvider.types';
import {tokenForAssetKey} from '../../asset-graph/Utils';
import {useAssetSelectionInput} from '../../asset-selection/input/useAssetSelectionInput';
import {useAllAssets} from '../../assets/AssetsCatalogTable';
import {AssetHealthStatus} from '../../graphql/types';
import {useQueryAndLocalStoragePersistedState} from '../../hooks/useQueryAndLocalStoragePersistedState';
import {useQueryPersistedState} from '../../hooks/useQueryPersistedState';
import {useSelectionReducer} from '../../hooks/useSelectionReducer';
import {useStateWithStorage} from '../../hooks/useStateWithStorage';
import {useBlockTraceUntilTrue} from '../../performance/TraceContext';
import {SyntaxError} from '../../selection/CustomErrorListener';
import {IndeterminateLoadingBar} from '../../ui/IndeterminateLoadingBar';
import {numberFormatter} from '../../ui/formatters';
import {buildRepoPathForHuman} from '../../workspace/buildRepoAddress';
import {statusToIconAndColor} from '../AssetHealthSummary';
import {AssetsEmptyState} from '../AssetsEmptyState';
import {LaunchAssetExecutionButton} from '../LaunchAssetExecutionButton';
import {asAssetKeyInput} from '../asInput';
import {AssetTableFragment} from '../types/AssetTableFragment.types';

export const AssetCatalogTableV2 = React.memo(() => {
  const {assets, loading: assetsLoading, error} = useAllAssets();
  useBlockTraceUntilTrue('useAllAssets', !assetsLoading);
  const trackEvent = useTrackEvent();

  const {favorites, loading: favoritesLoading} = useFavoriteAssets();

  const penultimateAssets = useMemo(() => {
    if (!favorites) {
      return assets ?? [];
    }
    return (assets ?? []).filter((asset) => favorites.has(tokenForAssetKey(asset.key)));
  }, [favorites, assets]);

  const [errorState, setErrorState] = useState<SyntaxError[]>([]);

  const {
    filterInput,
    filtered,
    loading: selectionLoading,
    setAssetSelection,
    assetSelection,
  } = useAssetSelectionInput<AssetTableFragment>({
    assets: penultimateAssets,
    assetsLoading: !assets && (assetsLoading || favoritesLoading),
    onErrorStateChange: useCallback(
      (errors: SyntaxError[]) => {
        if (errors !== errorState) {
          setErrorState(errors);
        }
      },
      [errorState],
    ),
  });

  const loading = selectionLoading && !filtered.length;

  const [sortBy, setSortBy] = useStateWithStorage<(typeof SORT_ITEMS)[number]['key']>(
    usePrefixedCacheKey('catalog-sortBy'),
    (json) => {
      if (['materialization_asc', 'materialization_desc', 'key_asc', 'key_desc'].includes(json)) {
        return json;
      }
      return 'materialization_asc';
    },
  );

  const {liveDataByNode} = useAssetsHealthData({
    assetKeys: useMemo(() => filtered.map((asset) => asAssetKeyInput(asset.key)), [filtered]),
    loading,
  });

  const healthDataLoading = useMemo(() => {
    return Object.values(liveDataByNode).length !== filtered.length;
  }, [liveDataByNode, filtered]);

  const [groupBy, setGroupBy] = useQueryAndLocalStoragePersistedState<AssetHealthGroupBy>({
    localStorageKey: usePrefixedCacheKey('catalog-groupBy'),
    isEmptyState: (state) => !state || state === AssetHealthGroupBy.code_location,
    decode: useCallback((qs: ParsedQs) => {
      if (qs.groupBy && GROUP_BY.includes(qs.groupBy as AssetHealthGroupBy)) {
        return qs.groupBy as AssetHealthGroupBy;
      }
      return AssetHealthGroupBy.health_status;
    }, []),
    encode: useCallback((b: AssetHealthGroupBy) => ({groupBy: b}), []),
  });

  const {assetsByAssetKey} = useAllAssets();

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
            return Array.from(
              new Set(
                [asset?.definition?.computeKind, ...(asset?.definition?.kinds ?? [])].filter(
                  Boolean,
                ) as string[],
              ),
            );
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
            return <HealthStatusHeaderRow {...props} status={props.group} />;
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
            return <HealthStatusHeaderRow {...props} status={props.group} />;
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
            return <HealthStatusHeaderRow {...props} status={props.group} />;
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
    Object.values(grouped).forEach((group) => {
      group.assets.sort(sortFn);
    });
    return grouped;
  }, [grouped, sortBy]);

  const [selectedTab, setSelectedTab] = useQueryPersistedState<string>({
    queryKey: 'selectedTab',
    defaults: {selectedTab: 'assets'},
    decode: (qs) =>
      qs.selectedTab && typeof qs.selectedTab === 'string' ? qs.selectedTab : 'assets',
    encode: (b) => ({selectedTab: b || 'assets'}),
  });

  const displayKeys = useMemo(() => {
    return Object.values(groupedAndSorted).flatMap((group) =>
      group.assets.map((asset) => tokenForAssetKey(asset.key)),
    );
  }, [groupedAndSorted]);

  const [{checkedIds: checkedDisplayKeys}, {onToggleFactory}] = useSelectionReducer(displayKeys);

  const onToggleGroup = useCallback(
    (group: string) => {
      return (checked: boolean) => {
        groupedAndSorted[group]?.assets.forEach((asset) => {
          const toggle = onToggleFactory(tokenForAssetKey(asset.key));
          toggle({checked, shiftKey: false});
        });
      };
    },
    [groupedAndSorted, onToggleFactory],
  );

  const setCurrentPage = useSetRecoilState(currentPageAtom);
  const {path} = useRouteMatch();
  useEffect(() => {
    setCurrentPage(({specificPath}) => ({
      specificPath,
      path: `${path}?view=AssetCatalogTableV2&selected_tab=${selectedTab}`,
    }));
  }, [path, setCurrentPage, selectedTab, trackEvent]);

  const onChangeTab = useCallback(
    (tab: string) => {
      setSelectedTab(tab);
      trackEvent('asset-selection-change-tab', {tab});
    },
    [setSelectedTab, trackEvent],
  );

  const {isFullScreen} = useFullScreen();

  const shouldShowCatalogAlerts = useShouldShowAssetCatalogAlerts();

  const tabs = useMemo(
    () => (
      <Box border="bottom">
        {isFullScreen ? null : (
          <Tabs
            onChange={onChangeTab}
            selectedTabId={selectedTab}
            style={{marginLeft: 24, marginRight: 24}}
          >
            <Tab id="assets" title="Assets" />
            <Tab id="lineage" title="Lineage" />
            <Tab id="insights" title="Insights" />
            {shouldShowCatalogAlerts ? <Tab id="alerts" title="Alert Policies" /> : null}
          </Tabs>
        )}
      </Box>
    ),
    [isFullScreen, onChangeTab, selectedTab, shouldShowCatalogAlerts],
  );

  const content = () => {
    if (error) {
      return <PythonErrorInfo error={error} />;
    }

    if (!assets?.length && !loading) {
      return (
        <Box padding={{vertical: 64}}>
          <AssetsEmptyState />
        </Box>
      );
    }
    if (favorites && filtered.length === 0 && !loading) {
      return (
        <Box padding={24}>
          <NonIdealState
            icon="star"
            title="No favorite assets"
            description="To add one, click the star in the asset view or choose 'Add to favorites' from the asset menu in the catalog."
          />
        </Box>
      );
    }
    switch (selectedTab) {
      case 'lineage':
        return (
          <AssetCatalogAssetGraph
            selection={assetSelection}
            onChangeSelection={setAssetSelection}
            tabs={tabs}
          />
        );
      case 'insights':
        return (
          <AssetCatalogInsights
            assets={filtered}
            selection={assetSelection}
            tabs={tabs}
            visibleSections={
              new Set(['rate-cards', 'performance-metrics', 'activity-charts', 'top-assets'])
            }
          />
        );
      case 'alerts':
        return <AssetCatalogAlerts tabs={tabs} selection={assetSelection} />;
      default:
        return (
          <Table
            assets={filtered}
            grouped={groupedAndSorted}
            loading={loading}
            selectionLoading={selectionLoading}
            healthDataLoading={healthDataLoading}
            tabs={tabs}
            sortBy={sortBy}
            setSortBy={setSortBy}
            groupBy={groupBy}
            setGroupBy={setGroupBy}
            checkedDisplayKeys={checkedDisplayKeys}
            onToggleFactory={onToggleFactory}
            onToggleGroup={onToggleGroup}
            allGroups={allGroups}
          />
        );
    }
  };

  const extraStyles =
    selectedTab === 'lineage'
      ? {
          gridTemplateColumns: 'minmax(500px, 1fr)',
          display: 'grid',
          gridTemplateRows: 'repeat(2, auto) minmax(0, 1fr)',
        }
      : {};
  return (
    <Box flex={{direction: 'column'}} style={{height: '100%', minHeight: 600, ...extraStyles}}>
      <Box
        flex={{direction: 'row', alignItems: 'center', gap: 8}}
        padding={{vertical: 12, horizontal: 24}}
        border={['insights', 'lineage'].includes(selectedTab) ? 'bottom' : undefined}
      >
        <Box flex={{grow: 1, shrink: 1}}>{filterInput}</Box>
        <CreateCatalogViewButton />
      </Box>
      {/* Lineage and Insights render their own loading bars */}
      {content()}
    </Box>
  );
});

AssetCatalogTableV2.displayName = 'AssetCatalogTableV2';

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

type TableProps<T extends string> = {
  assets: AssetTableFragment[] | undefined;
  grouped: AssetCatalogV2VirtualizedTableProps<T>['grouped'];
  loading: boolean;
  healthDataLoading: boolean;
  tabs: React.ReactNode;
  sortBy: (typeof SORT_ITEMS)[number]['key'];
  setSortBy: (sortBy: (typeof SORT_ITEMS)[number]['key']) => void;
  checkedDisplayKeys: Set<string>;
  onToggleFactory: (id: string) => (values: {checked: boolean; shiftKey: boolean}) => void;
  onToggleGroup: (group: T) => (checked: boolean) => void;
  selectionLoading: boolean;
  groupBy: AssetHealthGroupBy;
  setGroupBy: (groupBy: (typeof GROUP_BY_ITEMS)[number]['key']) => void;
  allGroups?: T[];
};

const Table = React.memo(
  <T extends string>({
    assets,
    grouped,
    loading,
    healthDataLoading,
    tabs,
    sortBy,
    setSortBy,
    checkedDisplayKeys,
    onToggleFactory,
    onToggleGroup,
    selectionLoading,
    groupBy,
    setGroupBy,
    allGroups: _allGroups,
  }: TableProps<T>) => {
    const scope = useMemo(() => {
      const list = (assets ?? []).filter((a): a is AssetWithDefinition => !!a.definition);
      const selected = list.filter((a) => checkedDisplayKeys.has(JSON.stringify(a.key.path)));
      return {
        selected: selected.map((a) => ({...a.definition, assetKey: a.key})),
      };
    }, [assets, checkedDisplayKeys]);

    const extraDropdownOptions = useCatalogExtraDropdownOptions({scope});

    const allGroups = useMemo(() => {
      return _allGroups ?? (Object.keys(grouped) as T[]);
    }, [_allGroups, grouped]);

    return (
      <>
        <IndeterminateLoadingBar
          $loading={loading || (healthDataLoading && isHealthGroupBy(groupBy)) || selectionLoading}
        />
        {tabs}
        <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
          <Box
            flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between'}}
            padding={{horizontal: 24, vertical: 12}}
            border="bottom"
          >
            <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
              <Subtitle1>
                {loading ? (
                  <Skeleton $width={200} $height={21} />
                ) : (
                  <>
                    {numberFormatter.format(assets?.length ?? 0)} asset
                    {ifPlural(assets?.length ?? 0, '', 's')}
                  </>
                )}
              </Subtitle1>
              {checkedDisplayKeys.size > 0 ? (
                <Popover
                  interactionKind="hover"
                  placement="bottom-start"
                  content={
                    <SelectedAssetsPopoverContent
                      checkedDisplayKeys={checkedDisplayKeys}
                      grouped={grouped}
                    />
                  }
                >
                  <Tag intent="primary">
                    {numberFormatter.format(checkedDisplayKeys.size)} selected
                  </Tag>
                </Popover>
              ) : null}
            </Box>
            <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
              <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
                <Body color={Colors.textLight()}>Group by</Body>
                <Select<(typeof GROUP_BY_ITEMS)[number]>
                  popoverProps={{
                    position: 'bottom-right',
                  }}
                  filterable={false}
                  activeItem={GROUP_BY_ITEMS.find((item) => item.key === groupBy)}
                  items={GROUP_BY_ITEMS}
                  itemRenderer={(item, props) => {
                    return (
                      <MenuItem
                        active={props.modifiers.active}
                        onClick={props.handleClick}
                        key={item.key}
                        icon={item.icon}
                        text={item.text}
                        style={{width: '300px'}}
                      />
                    );
                  }}
                  onItemSelect={(item) => setGroupBy(item.key)}
                >
                  <UnstyledButton $outlineOnHover style={{display: 'flex', padding: '6px 4px'}}>
                    {GROUP_BY_ITEMS.find((item) => item.key === groupBy)?.text}
                    <Icon name="arrow_drop_down" />
                  </UnstyledButton>
                </Select>
              </Box>
              <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
                <Body color={Colors.textLight()}>Sort by</Body>
                <Select<(typeof SORT_ITEMS)[number]>
                  popoverProps={{
                    position: 'bottom-right',
                  }}
                  filterable={false}
                  activeItem={ITEMS_BY_KEY[sortBy]}
                  items={SORT_ITEMS}
                  itemRenderer={(item, props) => {
                    return (
                      <MenuItem
                        active={props.modifiers.active}
                        onClick={props.handleClick}
                        key={item.key}
                        text={item.text}
                        style={{width: '300px'}}
                      />
                    );
                  }}
                  onItemSelect={(item) => setSortBy(item.key)}
                >
                  <UnstyledButton $outlineOnHover style={{display: 'flex', padding: '6px 4px'}}>
                    {ITEMS_BY_KEY[sortBy].text}
                    <Icon name="arrow_drop_down" />
                  </UnstyledButton>
                </Select>
              </Box>
              {loading ? (
                <Skeleton $width={300} $height={21} />
              ) : (
                <LaunchAssetExecutionButton
                  scope={scope}
                  additionalDropdownOptions={extraDropdownOptions}
                />
              )}
            </Box>
          </Box>
          <div style={{flex: 1, overflow: 'hidden'}}>
            <AssetCatalogV2VirtualizedTable
              allGroups={allGroups}
              grouped={grouped}
              loading={loading}
              healthDataLoading={healthDataLoading}
              checkedDisplayKeys={checkedDisplayKeys}
              onToggleFactory={onToggleFactory}
              onToggleGroup={onToggleGroup}
            />
          </div>
        </Box>
      </>
    );
  },
);
Table.displayName = 'Table';

type AssetWithDefinition = AssetTableFragment & {
  definition: NonNullable<AssetTableFragment['definition']>;
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

function groupByAttribute<T extends string>({
  liveDataByNode,
  getAttributes,
  renderGroupHeader,
}: {
  liveDataByNode: Record<string, AssetHealthFragment>;
  getAttributes: (asset: AssetHealthFragment) => T[];
  renderGroupHeader: Grouped<T>['renderGroupHeader'];
}): Record<T, Grouped<T>> {
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
}

function isHealthGroupBy(groupBy: AssetHealthGroupBy) {
  return [
    AssetHealthGroupBy.health_status,
    AssetHealthGroupBy.freshness_status,
    AssetHealthGroupBy.check_status,
  ].includes(groupBy);
}
