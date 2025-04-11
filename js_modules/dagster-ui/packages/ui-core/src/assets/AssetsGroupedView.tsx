import {
  Box,
  Colors,
  Container,
  Icon,
  IconName,
  IconWrapper,
  Inner,
  MiddleTruncate,
  Row,
  Tab,
  Tabs,
  ifPlural,
} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import {useMemo, useRef, useState} from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {assertUnreachable} from '../app/Util';
import {numberFormatter} from '../ui/formatters';
import {AssetTableFragment} from './types/AssetTableFragment.types';
import {
  linkToAssetTableWithAssetOwnerFilter,
  linkToAssetTableWithGroupFilter,
  linkToAssetTableWithKindFilter,
  linkToAssetTableWithTagFilter,
  linkToCodeLocation,
} from '../search/links';
import {buildRepoAddress, buildRepoPathForHuman} from '../workspace/buildRepoAddress';

type Property = 'owners' | 'groupName' | 'repository' | 'tags' | 'kinds';

export const AssetsGroupedView = ({assets}: {assets: AssetTableFragment[]}) => {
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
                    count: 0,
                    link: linkToAssetTableWithAssetOwnerFilter(owner),
                  };
                  acc.owners[owner.team]!.count++;
                  break;
                case 'UserAssetOwner':
                  acc.owners[owner.email] = acc.owners[owner.email] || {
                    count: 0,
                    link: linkToAssetTableWithAssetOwnerFilter(owner),
                  };
                  acc.owners[owner.email]!.count++;
                  break;
                default:
                  assertUnreachable(owner);
              }
            });
          }
          if (groupName) {
            acc.groupName[groupName] = acc.groupName[groupName] || {
              count: 0,
              link: linkToAssetTableWithGroupFilter({
                groupName,
                repositoryLocationName: repository?.location.name,
                repositoryName: repository?.name,
              }),
            };
            acc.groupName[groupName]!.count++;
          }
          if (repository) {
            const name = buildRepoPathForHuman(repository.name, repository.location.name);
            acc.repository[name] = acc.repository[name] || {
              count: 0,
              link: linkToCodeLocation(buildRepoAddress(repository.name, repository.location.name)),
            };
            acc.repository[name]!.count++;
          }
          if (tags) {
            tags.forEach((tag) => {
              const stringValue = `${tag.key}${tag.value ? ': ' + tag.value : ''}`;
              acc.tags[stringValue] = acc.tags[stringValue] || {
                count: 0,
                link: linkToAssetTableWithTagFilter(tag),
              };
              acc.tags[stringValue]!.count++;
            });
          }
          if (kinds) {
            kinds.forEach((kind) => {
              acc.kinds[kind] = acc.kinds[kind] || {
                count: 0,
                link: linkToAssetTableWithKindFilter(kind),
              };
              acc.kinds[kind]!.count++;
            });
          }
          return acc;
        },
        {
          owners: {} as Record<string, {count: number; link: string}>,
          groupName: {} as Record<string, {count: number; link: string}>,
          repository: {} as Record<string, {count: number; link: string}>,
          tags: {} as Record<string, {count: number; link: string}>,
          kinds: {} as Record<string, {count: number; link: string}>,
        },
      ),
    [assets],
  );

  const [selectedTab, setSelectedTab] = useState<Property>('groupName');

  const tabs = useMemo(() => {
    return Object.entries(propertyToLabelAndIcon).map(([key]) => {
      const {label} = propertyToLabelAndIcon[key as Property];
      return <Tab key={key} id={key} title={label} />;
    });
  }, []);

  const items = groupedAssets[selectedTab as Property];

  return (
    <Box>
      <Box border="bottom">
        <Tabs
          onChange={setSelectedTab}
          selectedTabId={selectedTab}
          style={{marginLeft: 24, marginRight: 24}}
        >
          {tabs}
        </Tabs>
      </Box>
      <Table items={items} icon={propertyToLabelAndIcon[selectedTab].icon} />
    </Box>
  );
};

const Table = ({
  items,
  icon,
}: {
  items: Record<string, {count: number; link: string}>;
  icon: IconName;
}) => {
  const rows = useMemo(
    () => Object.entries(items).sort(([keyA], [keyB]) => keyA.localeCompare(keyB)),
    [items],
  );

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
          const [itemKey, {count, link}] = rows[index]!;
          return (
            <Row key={key} $height={size} $start={start}>
              <div ref={rowVirtualizer.measureElement} data-index={index}>
                <RowWrapper as={Link} to={link}>
                  <Box
                    padding={{horizontal: 24, vertical: 12}}
                    flex={{alignItems: 'center', gap: 8, justifyContent: 'space-between'}}
                    border="bottom"
                  >
                    <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
                      <Icon name={icon} color={Colors.textLight()} />
                      <MiddleTruncate text={itemKey} />
                    </Box>
                    <span>
                      {numberFormatter.format(count)} asset
                      {ifPlural(count, '', 's')}
                    </span>
                  </Box>
                </RowWrapper>
              </div>
            </Row>
          );
        })}
      </Inner>
    </Container>
  );
};

const RowWrapper = styled.div`
  color: ${Colors.textLight()};
  cursor: pointer;
  :hover {
    &,
    ${IconWrapper} {
      color: ${Colors.textDefault()};
    }
    ${IconWrapper} {
      background: ${Colors.textDefault()};
    }
  }
`;

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
