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
import {useDeferredValue, useMemo, useRef, useState} from 'react';
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
import {ViewType} from './util';
import {assertUnreachable} from '../../app/Util';
import {usePrefixedCacheKey} from '../../app/usePrefixedCacheKey';
import {useStateWithStorage} from '../../hooks/useStateWithStorage';
import {InsightsIcon} from '../../insights/InsightsIcon';
import {
  linkToAssetTableWithAssetOwnerFilter,
  linkToAssetTableWithGroupFilter,
  linkToAssetTableWithKindFilter,
  linkToAssetTableWithTagFilter,
  linkToCodeLocation,
} from '../../search/links';
import {numberFormatter} from '../../ui/formatters';
import {weakMapMemoize} from '../../util/weakMapMemoize';
import {buildRepoAddress, buildRepoPathForHuman} from '../../workspace/buildRepoAddress';
import {AssetTableFragment} from '../types/AssetTableFragment.types';
import {useAllAssets} from '../useAllAssets';

type Property = 'owners' | 'groupName' | 'repository' | 'tags' | 'kinds';

export const AssetsGroupedView = ({assets}: {assets: AssetTableFragment[]}) => {
  const {privateViews, publicViews} = useCatalogViews();

  const groupedAssets = useMemo(
    () =>
      assets.reduce(
        (acc, asset) => {
          const {definition} = asset;
          if (!definition) {
            return acc;
          }
          const {owners, groupName, repository, tags, kinds} = definition;
          if (owners) {
            owners.forEach((owner) => {
              switch (owner.__typename) {
                case 'TeamAssetOwner':
                  acc.owners[owner.team] = acc.owners[owner.team] || {
                    assets: [],
                    label: owner.team,
                    link: linkToAssetTableWithAssetOwnerFilter(owner),
                  };
                  acc.owners[owner.team]!.assets.push(asset);
                  break;
                case 'UserAssetOwner':
                  acc.owners[owner.email] = acc.owners[owner.email] || {
                    assets: [],
                    label: owner.email,
                    link: linkToAssetTableWithAssetOwnerFilter(owner),
                  };
                  acc.owners[owner.email]!.assets.push(asset);
                  break;
                default:
                  assertUnreachable(owner);
              }
            });
          }
          if (groupName) {
            acc.groupName[groupName] = acc.groupName[groupName] || {
              assets: [],
              label: groupName,
              link: linkToAssetTableWithGroupFilter({
                groupName,
                repositoryLocationName: repository?.location.name,
                repositoryName: repository?.name,
              }),
            };
            acc.groupName[groupName]!.assets.push(asset);
          }
          if (repository) {
            const name = buildRepoPathForHuman(repository.name, repository.location.name);
            acc.repository[name] = acc.repository[name] || {
              assets: [],
              label: name,
              link: linkToCodeLocation(buildRepoAddress(repository.name, repository.location.name)),
            };
            acc.repository[name]!.assets.push(asset);
          }
          if (tags) {
            tags.forEach((tag) => {
              const stringValue = `${tag.key}${tag.value ? ': ' + tag.value : ''}`;
              acc.tags[stringValue] = acc.tags[stringValue] || {
                assets: [],
                label: stringValue,
                link: linkToAssetTableWithTagFilter(tag),
              };
              acc.tags[stringValue]!.assets.push(asset);
            });
          }
          if (kinds) {
            kinds.forEach((kind) => {
              acc.kinds[kind] = acc.kinds[kind] || {
                assets: [],
                label: kind,
                link: linkToAssetTableWithKindFilter(kind),
              };
              acc.kinds[kind]!.assets.push(asset);
            });
          }
          return acc;
        },
        {
          owners: {} as Record<string, {label: string; assets: AssetTableFragment[]; link: string}>,
          groupName: {} as Record<
            string,
            {label: string; assets: AssetTableFragment[]; link: string}
          >,
          repository: {} as Record<
            string,
            {label: string; assets: AssetTableFragment[]; link: string}
          >,
          tags: {} as Record<string, {label: string; assets: AssetTableFragment[]; link: string}>,
          kinds: {} as Record<string, {label: string; assets: AssetTableFragment[]; link: string}>,
        },
      ),
    [assets],
  );

  const [selectedTab, setSelectedTab] = useState<Property | 'selections'>('selections');

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
          items: [ALL_ASSETS_VIEW, ...publicViews],
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
      {isList ? (
        isSelections ? (
          <SectionedList sections={sections} />
        ) : (
          <List rows={listItems} />
        )
      ) : isSelections ? (
        <SectionedGrid sections={sections} tileGap={TILE_GAP} tileWidth={TILE_WIDTH} />
      ) : (
        <Box padding={{horizontal: 24, vertical: 24}}>
          <Grid tiles={tiles} tileGap={TILE_GAP} tileWidth={TILE_WIDTH} />
        </Box>
      )}
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
      .sort(([keyA], [keyB]) => keyA.localeCompare(keyB))
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
    renderItem: (item: ViewType) => renderSelectionListItem(item, assetsByAssetKey),
    renderTile: (item: ViewType) => renderSelectionTile(item, assetsByAssetKey),
  };
}

function renderSelectionListItem(
  item: ViewType,
  assetsByAssetKey: Map<string, AssetTableFragment>,
) {
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
      assets={item.assets.map((assetKey) => assetsByAssetKey.get(assetKey)!).filter(Boolean)}
      icon={<Icon name={item.icon as IconName} size={16} />}
      label={item.name}
      link={item.link}
      menu={<Menu />}
    />
  );
}

function renderSelectionTile(item: ViewType, assetsByAssetKey: Map<string, AssetTableFragment>) {
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
}

const ALL_ASSETS_VIEW = {
  __typename: 'CatalogView' as const,
  id: 'all-assets',
  creatorId: 'dagster',
  name: 'All assets',
  description: 'All assets',
  isPrivate: false,
  selection: {
    __typename: 'CatalogViewSelection' as const,
    kinds: [],
    columns: [],
    tableNames: [],
    querySelection: null,
    tags: [],
    owners: [],
    groups: [],
    codeLocations: [],
    columnTags: [],
  },
  link: '/assets',
  icon: 'asset',
};
