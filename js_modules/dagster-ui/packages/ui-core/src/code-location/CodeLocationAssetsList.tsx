import {
  Box,
  Colors,
  Icon,
  IconWrapper,
  NonIdealState,
  SpinnerWithText,
  Tag,
  TextInput,
} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import {ChangeEvent, useCallback, useMemo, useRef, useState} from 'react';
import styled from 'styled-components';

import {SearchableListRow} from './CodeLocationSearchableList';
import {useQuery} from '../apollo-client';
import {displayNameForAssetKey} from '../asset-graph/Utils';
import {assetDetailsPathForKey} from '../assets/assetDetailsPathForKey';
import {useAssetSearch} from '../assets/useAssetSearch';
import {Container, HeaderCell, HeaderRow, Inner, Row} from '../ui/VirtualizedTable';
import {WORKSPACE_ASSETS_QUERY} from '../workspace/WorkspaceAssetsQuery';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';
import {
  WorkspaceAssetsQuery,
  WorkspaceAssetsQueryVariables,
} from '../workspace/types/WorkspaceAssetsQuery.types';
import {useFlattenedGroupedAssetList} from '../workspace/useFlattenedGroupedAssetList';

const UNGROUPED_NAME = 'UNGROUPED';
const ROW_HEIGHT = 44;

interface Props {
  repoAddress: RepoAddress;
}

export const CodeLocationAssetsList = ({repoAddress}: Props) => {
  const [searchValue, setSearchValue] = useState('');

  const repoName = repoAddressAsHumanString(repoAddress);
  const selector = repoAddressToSelector(repoAddress);
  const queryResultOverview = useQuery<WorkspaceAssetsQuery, WorkspaceAssetsQueryVariables>(
    WORKSPACE_ASSETS_QUERY,
    {
      variables: {selector},
    },
  );
  const {data, loading} = queryResultOverview;

  const assetNodes = useMemo(() => {
    if (data?.repositoryOrError.__typename === 'Repository') {
      return data.repositoryOrError.assetNodes;
    }
    return [];
  }, [data]);

  const filteredBySearch = useAssetSearch(searchValue, assetNodes);
  const {flattened, expandedKeys, onToggle} = useFlattenedGroupedAssetList({
    repoAddress,
    assets: filteredBySearch,
  });

  const onChange = useCallback((e: ChangeEvent<HTMLInputElement>) => {
    setSearchValue(e.target.value);
  }, []);

  const containerRef = useRef<HTMLDivElement | null>(null);
  const rowVirtualizer = useVirtualizer({
    count: flattened.length,
    getScrollElement: () => containerRef.current,
    estimateSize: () => ROW_HEIGHT,
    overscan: 10,
  });

  const totalHeight = rowVirtualizer.getTotalSize();
  const virtualItems = rowVirtualizer.getVirtualItems();

  const content = () => {
    if (loading && !data) {
      return (
        <Box flex={{direction: 'row', justifyContent: 'center'}} padding={32}>
          <SpinnerWithText label="Loading assets…" />
        </Box>
      );
    }

    if (!filteredBySearch.length) {
      if (searchValue.trim().length > 0) {
        return (
          <Box padding={{top: 20}}>
            <NonIdealState
              icon="search"
              title="No matching assets"
              description={
                <div>
                  No assets matching <strong>{searchValue}</strong> were found in {repoName}
                </div>
              }
            />
          </Box>
        );
      }

      return (
        <Box padding={{top: 20}}>
          <NonIdealState
            icon="search"
            title="No assets"
            description={`No assets were found in ${repoName}`}
          />
        </Box>
      );
    }

    return (
      <Container ref={containerRef}>
        <HeaderRow templateColumns="1fr" sticky>
          <HeaderCell>Name</HeaderCell>
        </HeaderRow>
        <Inner $totalHeight={totalHeight}>
          {virtualItems.map(({index, key, size, start}) => {
            const item = flattened[index]!;
            if (item.type === 'group') {
              return (
                <GroupNameRow
                  key={key}
                  height={size}
                  start={start}
                  expanded={expandedKeys.has(item.name)}
                  groupName={item.name}
                  assetCount={item.assetCount}
                  onToggle={onToggle}
                />
              );
            }

            const {path} = item.definition.assetKey;
            return (
              <Row key={key} $height={size} $start={start}>
                <SearchableListRow
                  iconName="asset"
                  label={displayNameForAssetKey({path})}
                  path={assetDetailsPathForKey({path})}
                />
              </Row>
            );
          })}
        </Inner>
      </Container>
    );
  };

  return (
    <Box flex={{direction: 'column'}} style={{overflow: 'hidden'}}>
      <Box padding={{vertical: 8, horizontal: 24}}>
        <TextInput
          value={searchValue}
          onChange={onChange}
          placeholder="Search assets by key…"
          style={{width: '300px'}}
          icon="search"
        />
      </Box>
      <div style={{flex: 1, overflow: 'hidden'}}>{content()}</div>
    </Box>
  );
};

interface GroupNameRowProps {
  groupName: string;
  assetCount: number;
  expanded: boolean;
  height: number;
  start: number;
  onToggle: (groupName: string) => void;
}

const GroupNameRow = (props: GroupNameRowProps) => {
  const {groupName, assetCount, expanded, height, start, onToggle} = props;
  return (
    <ClickableRow
      $height={height}
      $start={start}
      onClick={() => onToggle(groupName)}
      $open={expanded}
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.code === 'Space' || e.code === 'Enter') {
          e.preventDefault();
          onToggle(groupName);
        }
      }}
    >
      <Box
        background={Colors.backgroundLight()}
        flex={{direction: 'row', alignItems: 'center', gap: 8, justifyContent: 'space-between'}}
        padding={{horizontal: 24}}
        border="bottom"
        style={{height: '100%'}}
      >
        <Box flex={{alignItems: 'center', gap: 8}}>
          <Icon name="asset_group" />
          {groupName === UNGROUPED_NAME ? (
            <div>Ungrouped assets</div>
          ) : (
            <strong>{groupName}</strong>
          )}
        </Box>
        <Box flex={{direction: 'row', alignItems: 'center', gap: 12}}>
          <Tag>{assetCount === 1 ? '1 asset' : `${assetCount} assets`}</Tag>
          <Icon name="arrow_drop_down" size={20} />
        </Box>
      </Box>
    </ClickableRow>
  );
};

const ClickableRow = styled(Row)<{$open: boolean}>`
  cursor: pointer;

  :focus,
  :active {
    outline: none;
  }

  ${IconWrapper}[aria-label="arrow_drop_down"] {
    transition: transform 100ms linear;
    ${({$open}) => ($open ? null : `transform: rotate(-90deg);`)}
  }
`;
