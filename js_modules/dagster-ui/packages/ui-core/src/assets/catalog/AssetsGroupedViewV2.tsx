import {Box, Colors, Container, Icon, IconName, Inner, Tab, Tabs} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import React, {useMemo, useRef} from 'react';
import {useCatalogViews} from 'shared/assets/catalog/useCatalogViews.oss';

import {
  AssetSelectionSummaryListItem,
  AssetSelectionSummaryListItemFromSelection,
} from './AssetSelectionSummaryListItemV2';
import {ViewType, getGroupedAssets} from './util';
import {COMMON_COLLATOR} from '../../app/Util';
import {KNOWN_TAGS, KnownTagType} from '../../graph/OpTags';
import {useQueryPersistedState} from '../../hooks/useQueryPersistedState';
import {InsightsIcon} from '../../insights/InsightsIcon';
import {LoadingSpinner} from '../../ui/Loading';
import {weakMapMemoize} from '../../util/weakMapMemoize';
import {AssetTableFragment} from '../types/AssetTableFragment.types';
import {useAllAssets} from '../useAllAssets';

const PROPERTIES = ['owners', 'groupName', 'repository', 'tags', 'kinds'] as const;
type Property = (typeof PROPERTIES)[number];

export const AssetsGroupedView = ({assets}: {assets: AssetTableFragment[]}) => {
  const {privateViews, publicViews, loading: loadingCatalogViews} = useCatalogViews();

  const groupedAssets = useMemo(() => getGroupedAssets(assets), [assets]);

  const [selectedTab, setSelectedTab] = useQueryPersistedState<Property | 'selections'>({
    queryKey: 'tab',
    behavior: 'push',
    encode: (value) => ({tab: value}),
    decode: (qs) => {
      if (typeof qs.tab === 'string' && PROPERTIES.includes(qs.tab as Property)) {
        return qs.tab as Property;
      }
      return 'selections';
    },
  });

  const tabs = useMemo(() => {
    const ossTabs = Object.entries(propertyToLabelAndIcon).map(([key]) => {
      const {label} = propertyToLabelAndIcon[key as Property];
      return <Tab key={key} id={key} title={label} />;
    });
    if (privateViews.length > 0 || publicViews.length > 0) {
      return [<Tab key="selections" id="selections" title="Selections" />, ...ossTabs];
    }
    return ossTabs;
  }, [privateViews, publicViews]);

  const {assetsByAssetKey} = useAllAssets();

  // Build flat list of saved selections (private + shared), excluding Favorites
  const savedSelectionRows = useMemo(() => {
    if (selectedTab !== 'selections') {
      return [] as React.ReactNode[];
    }
    const merged = [...privateViews, ...publicViews].filter(
      (v) => v.__typename !== 'FavoritesView' && v.id !== 'all-assets',
    );
    merged.sort((a, b) => COMMON_COLLATOR.compare(a.name, b.name));
    return merged.map((item, index) => (
      <SelectionListItem
        key={item.id}
        index={index}
        item={item}
        assetsByAssetKey={assetsByAssetKey}
      />
    ));
  }, [selectedTab, privateViews, publicViews, assetsByAssetKey]);

  const listItems = useMemo(() => {
    if (selectedTab === 'selections') {
      return [];
    }
    return getListItems(groupedAssets[selectedTab], selectedTab);
  }, [groupedAssets, selectedTab]);

  const isSelections = selectedTab === 'selections';

  function content() {
    if (loadingCatalogViews && selectedTab === 'selections') {
      return <LoadingSpinner />;
    }

    if (isSelections) {
      return <List rows={savedSelectionRows} />;
    }
    return <List rows={listItems} />;
  }

  return (
    <Box>
      <Box>
        <Box
          flex={{direction: 'row', alignItems: 'center', gap: 8, justifyContent: 'space-between'}}
          padding={{horizontal: 16}}
          style={{borderBottom: `1px solid ${Colors.keylineDefault()}`}}
        >
          <Tabs onChange={setSelectedTab} selectedTabId={selectedTab}>
            {tabs}
          </Tabs>
          <Box />
        </Box>
      </Box>
      {content()}
    </Box>
  );
};

const getListItems = weakMapMemoize(
  (
    items: Record<string, {label: string; assets: AssetTableFragment[]; link: string}>,
    selectedTab: Property,
  ) => {
    return Object.entries(items)
      .sort(([keyA], [keyB]) => COMMON_COLLATOR.compare(keyA, keyB))
      .map(([key, {label, assets, link}], index) => {
        const icon = (
          <InsightsIcon
            name={
              selectedTab === 'kinds' && KNOWN_TAGS[label as KnownTagType]
                ? (label as KnownTagType)
                : propertyToLabelAndIcon[selectedTab].icon
            }
            size={16}
          />
        );
        return (
          <AssetSelectionSummaryListItem
            key={key}
            label={label}
            icon={icon}
            link={link}
            assets={assets}
            index={index}
          />
        );
      });
  },
);

const List = ({rows}: {rows: React.ReactNode[]}) => {
  const scrollWrapperRef = useRef<HTMLDivElement | null>(null);
  const rowVirtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => scrollWrapperRef.current,
    estimateSize: () => 28,
    overscan: 5,
  });

  const rowItems = rowVirtualizer.getVirtualItems();
  const totalHeight = rowVirtualizer.getTotalSize();

  return (
    <Container ref={scrollWrapperRef} style={{maxHeight: '600px', overflowY: 'auto'}}>
      <Inner $totalHeight={totalHeight}>
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            transform: `translateY(${rowItems[0]?.start ?? 0}px)`,
          }}
        >
          {rowItems.map(({index, key}) => {
            // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
            const row = rows[index]!;
            return (
              <div key={key} ref={rowVirtualizer.measureElement} data-index={index}>
                {row}
              </div>
            );
          })}
        </div>
      </Inner>
    </Container>
  );
};

const propertyToLabelAndIcon: Record<Property, {label: string; icon: IconName}> = {
  groupName: {
    label: 'Groups',
    icon: 'asset_group',
  },
  kinds: {
    label: 'Kinds',
    icon: 'compute_kind',
  },
  owners: {
    label: 'Owners',
    icon: 'account_circle',
  },
  tags: {
    label: 'Tags',
    icon: 'tag',
  },
  repository: {
    label: 'Code locations',
    icon: 'folder',
  },
};

// Removed accordion sections and create button; selections now render as a flat list

const SelectionListItem = React.memo(
  ({
    index,
    item,
    assetsByAssetKey,
  }: {
    index: number;
    item: ViewType;
    assetsByAssetKey: Map<string, AssetTableFragment>;
  }) => {
    if (item.__typename === 'CatalogView') {
      return <AssetSelectionSummaryListItemFromSelection index={index} item={item} />;
    }
    return (
      <AssetSelectionSummaryListItem
        index={index}
        assets={item.assets
          // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
          .map((assetKey: string) => assetsByAssetKey.get(assetKey)!)
          .filter(Boolean)}
        icon={<Icon name={item.icon as IconName} size={16} />}
        label={item.name}
        link={item.link}
      />
    );
  },
);

SelectionListItem.displayName = 'SelectionListItem';

// Removed grid tiles for selections
