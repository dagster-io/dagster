import {
  Box,
  Colors,
  Container,
  Icon,
  IconName,
  Inner,
  Menu,
  MenuItem,
  Popover,
  Row,
  Subtitle,
  Tab,
  Tabs,
  UnstyledButton,
} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import React, {useDeferredValue, useMemo, useRef} from 'react';
import {CreateCatalogViewButton} from 'shared/assets/CreateCatalogViewButton.oss';
import {useCatalogViews} from 'shared/assets/catalog/useCatalogViews.oss';

import {
  AssetSelectionSummaryListItem,
  AssetSelectionSummaryListItemFromSelection,
} from './AssetSelectionSummaryListItem';
import {
  AssetSelectionSummaryTile,
  AssetSelectionSummaryTileFromSelection,
  TILE_GAP,
  TILE_WIDTH,
} from './AssetSelectionSummaryTile';
import {Grid, SectionedGrid, SectionedList} from './ListGridViews';
import {ViewType, getGroupedAssets} from './util';
import {COMMON_COLLATOR} from '../../app/Util';
import {usePrefixedCacheKey} from '../../app/usePrefixedCacheKey';
import {useQueryPersistedState} from '../../hooks/useQueryPersistedState';
import {useStateWithStorage} from '../../hooks/useStateWithStorage';
import {InsightsIcon} from '../../insights/InsightsIcon';
import {LoadingSpinner} from '../../ui/Loading';
import {numberFormatter} from '../../ui/formatters';
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
      return [<Tab key="selections" id="selections" title="Saved selections" />, ...ossTabs];
    }
    return ossTabs;
  }, [privateViews, publicViews]);

  const items = groupedAssets[selectedTab as Property];

  const key = usePrefixedCacheKey('catalog-display-as');

  const [displayAs, setDisplayAs] = useStateWithStorage<'Grid' | 'List'>(key, (value) =>
    value === 'List' ? 'List' : 'Grid',
  );

  const {assetsByAssetKey} = useAllAssets();

  const sections = useMemo(() => {
    if (selectedTab === 'selections') {
      return [
        createSelectionSection({
          id: 'private-selections',
          icon: 'lock',
          label: 'Private selections',
          items: privateViews,
          displayAs,
          border: 'bottom',
          assetsByAssetKey,
          children: <CreateCatalogViewButton label="Create" alwaysVisible />,
        }),
        createSelectionSection({
          id: 'public-selections',
          icon: 'globe',
          label: 'Public selections',
          displayAs,
          items: publicViews,
          border: 'top-and-bottom',
          assetsByAssetKey,
          children: <CreateCatalogViewButton label="Create" alwaysVisible />,
        }),
      ];
    }
    return [];
  }, [assetsByAssetKey, privateViews, publicViews, selectedTab, displayAs]);

  const tiles = useMemo(() => {
    if (selectedTab === 'selections') {
      return [];
    }
    return getListItems(items, selectedTab, displayAs);
  }, [items, selectedTab, displayAs]);

  const listItems = useMemo(() => {
    if (selectedTab === 'selections') {
      return [];
    }
    return getListItems(groupedAssets[selectedTab], selectedTab, displayAs);
  }, [displayAs, groupedAssets, selectedTab]);

  const isSelections = selectedTab === 'selections';
  const isList = displayAs === 'List';

  function content() {
    if (loadingCatalogViews && selectedTab === 'selections') {
      return <LoadingSpinner />;
    }

    if (isList) {
      if (isSelections) {
        return <SectionedList sections={sections} />;
      }
      return <List rows={listItems} />;
    }

    if (isSelections) {
      return <SectionedGrid sections={sections} tileGap={TILE_GAP} tileWidth={TILE_WIDTH} />;
    }

    return (
      <Box padding={{horizontal: 24, vertical: 24}}>
        <Grid tiles={tiles} tileGap={TILE_GAP} tileWidth={TILE_WIDTH} />
      </Box>
    );
  }

  return (
    <Box>
      <Box border="bottom">
        <Box
          flex={{direction: 'row', alignItems: 'center', gap: 8, justifyContent: 'space-between'}}
          margin={{horizontal: 24}}
        >
          <Tabs onChange={setSelectedTab} selectedTabId={selectedTab}>
            {tabs}
          </Tabs>
          <Box flex={{direction: 'row', alignItems: 'center', gap: 2}}>
            Display as
            <Popover
              content={
                <Menu>
                  <MenuItem text="Grid" onClick={() => setDisplayAs('Grid')} />
                  <MenuItem text="List" onClick={() => setDisplayAs('List')} />
                </Menu>
              }
            >
              <UnstyledButton $outlineOnHover style={{padding: 8, borderRadius: 4}}>
                <Box flex={{direction: 'row', alignItems: 'center', gap: 2}}>
                  {displayAs}
                  <Icon name="arrow_drop_down" />
                </Box>
              </UnstyledButton>
            </Popover>
          </Box>
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
    displayAs: 'List' | 'Grid',
  ) => {
    return Object.entries(items)
      .sort(([keyA], [keyB]) => COMMON_COLLATOR.compare(keyA, keyB))
      .map(([key, {label, assets, link}]) =>
        displayAs === 'List' ? (
          <AssetSelectionSummaryListItem
            key={key}
            label={label}
            icon={<Icon name={propertyToLabelAndIcon[selectedTab].icon} size={16} />}
            link={link}
            assets={assets}
            menu={<Menu />}
          />
        ) : (
          <AssetSelectionSummaryTile
            key={key}
            label={label}
            assets={assets}
            icon={<Icon name={propertyToLabelAndIcon[selectedTab].icon} size={16} />}
            link={link}
          />
        ),
      );
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
        {rowItems.map(({index, key, size, start}) => {
          const row = rows[index]!;
          return (
            <Row key={key} $height={size} $start={start}>
              <div ref={rowVirtualizer.measureElement} data-index={index}>
                {row}
              </div>
            </Row>
          );
        })}
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

// DRY: Shared Section Header for Selections
const SelectionSectionHeader = ({
  icon,
  label,
  count,
  border,
  isOpen,
  toggleOpen,
  children,
  displayAs,
}: {
  icon: IconName;
  label: string;
  count: number;
  border: 'top-and-bottom' | 'bottom';
  isOpen: boolean;
  toggleOpen: () => void;
  children?: React.ReactNode;
  displayAs: 'List' | 'Grid';
}) => {
  const actuallyOpen = useDeferredValue(isOpen);
  return (
    <Box padding={{bottom: actuallyOpen && displayAs === 'Grid' ? 24 : 0}}>
      <Box
        flex={{
          direction: 'row',
          alignItems: 'center',
          gap: 8,
          justifyContent: 'space-between',
        }}
        padding={{horizontal: 24, vertical: 2}}
        style={{height: 44}}
        background={Colors.backgroundLight()}
        border={border}
      >
        <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
          <Icon name={icon} />
          <Subtitle>
            {label} ({numberFormatter.format(count)})
          </Subtitle>
          <UnstyledButton
            onClick={(e) => {
              e.stopPropagation();
              toggleOpen();
            }}
            onDoubleClick={(e) => {
              e.stopPropagation();
            }}
            onKeyDown={(e) => {
              if (e.code === 'Space') {
                e.preventDefault();
              }
            }}
            style={{cursor: 'pointer', width: 18}}
          >
            <Icon
              name="arrow_drop_down"
              style={{transform: isOpen ? 'rotate(0deg)' : 'rotate(-90deg)'}}
            />
          </UnstyledButton>
        </Box>
        {children}
      </Box>
    </Box>
  );
};

function createSelectionSection({
  id,
  icon,
  label,
  items,
  border,
  children,
  displayAs,
  assetsByAssetKey,
}: {
  id: string;
  icon: IconName;
  label: string;
  items: ViewType[];
  border: 'top-and-bottom' | 'bottom';
  assetsByAssetKey: Map<string, AssetTableFragment>;
  children?: React.ReactNode;
  displayAs: 'List' | 'Grid';
}) {
  return {
    id,
    items,
    renderSectionHeader: ({isOpen, toggleOpen}: {isOpen: boolean; toggleOpen: () => void}) => (
      <SelectionSectionHeader
        key={id}
        icon={icon}
        label={label}
        count={items.length}
        border={border}
        isOpen={isOpen}
        toggleOpen={toggleOpen}
        displayAs={displayAs}
      >
        {children}
      </SelectionSectionHeader>
    ),
    renderItem: (item: ViewType) => (
      <SelectionListItem item={item} assetsByAssetKey={assetsByAssetKey} key={item.id} />
    ),
    renderTile: (item: ViewType) => (
      <SelectionTile item={item} assetsByAssetKey={assetsByAssetKey} key={item.id} />
    ),
  };
}

const SelectionListItem = React.memo(
  ({
    item,
    assetsByAssetKey,
  }: {
    item: ViewType;
    assetsByAssetKey: Map<string, AssetTableFragment>;
  }) => {
    if (item.__typename === 'CatalogView') {
      return (
        <AssetSelectionSummaryListItemFromSelection
          item={item}
          menu={<Menu />}
          icon={<Icon name={item.icon as IconName} size={16} />}
        />
      );
    }
    return (
      <AssetSelectionSummaryListItem
        assets={item.assets
          .map((assetKey: string) => assetsByAssetKey.get(assetKey)!)
          .filter(Boolean)}
        icon={<Icon name={item.icon as IconName} size={16} />}
        label={item.name}
        link={item.link}
        menu={<Menu />}
      />
    );
  },
);

const SelectionTile = React.memo(
  ({
    item,
    assetsByAssetKey,
  }: {
    item: ViewType;
    assetsByAssetKey: Map<string, AssetTableFragment>;
  }) => {
    return item.__typename === 'FavoritesView' ? (
      <AssetSelectionSummaryTile
        icon={<Icon name={item.icon as IconName} size={24} />}
        label={item.name}
        assets={item.assets.map((assetKey: any) => assetsByAssetKey.get(assetKey)!).filter(Boolean)}
        link={item.link}
      />
    ) : (
      <AssetSelectionSummaryTileFromSelection
        icon={<InsightsIcon name={item.icon as IconName} size={24} />}
        label={item.name}
        selection={item.selection.querySelection ?? ''}
        link={item.link}
      />
    );
  },
);
