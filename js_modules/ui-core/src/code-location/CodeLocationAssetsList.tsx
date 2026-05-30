import {
  Box,
  Colors,
  Icon,
  NonIdealState,
  SpinnerWithText,
  Tag,
  TextInput,
} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import clsx from 'clsx';
import {ChangeEvent, useCallback, useContext, useRef, useState} from 'react';

import {SearchableListRow} from './CodeLocationSearchableList';
import styles from './css/CodeLocationAssetsList.module.css';
import {displayNameForAssetKey} from '../asset-graph/Utils';
import {assetDetailsPathForKey} from '../assets/assetDetailsPathForKey';
import {useAssetSearch} from '../assets/useAssetSearch';
import {Container, HeaderCell, HeaderRow, Inner, Row} from '../ui/VirtualizedTable';
import {WorkspaceContext} from '../workspace/WorkspaceContext/WorkspaceContext';
import {useRepository} from '../workspace/WorkspaceContext/util';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';
import {useFlattenedGroupedAssetList} from '../workspace/useFlattenedGroupedAssetList';

const UNGROUPED_NAME = 'UNGROUPED';
const ROW_HEIGHT = 44;

interface Props {
  repoAddress: RepoAddress;
  expandAllGroups?: boolean;
}

export const CodeLocationAssetsList = ({repoAddress, expandAllGroups = false}: Props) => {
  const [searchValue, setSearchValue] = useState('');

  const repoName = repoAddressAsHumanString(repoAddress);

  // Asset data for every code location is already loaded by the workspace bootstrap
  // (LocationWorkspaceAssetsQuery, gated on assetManifest in #23365). Read from the
  // shared context instead of issuing a separate Repository.assetNodes query.
  const {loadingAssets} = useContext(WorkspaceContext);
  const repo = useRepository(repoAddress);
  const assetNodes = repo?.repository.assetNodes ?? [];

  const filteredBySearch = useAssetSearch(searchValue, assetNodes);
  const {flattened, expandedKeys, onToggle} = useFlattenedGroupedAssetList({
    repoAddress,
    assets: filteredBySearch,
    expandAllGroups,
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
    if (loadingAssets && !repo) {
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
            // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
            const item = flattened[index]!;
            if (item.type === 'group') {
              return (
                <GroupNameRow
                  key={key}
                  canToggle={!expandAllGroups}
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
  canToggle: boolean;
  onToggle: (groupName: string) => void;
}

const GroupNameRow = (props: GroupNameRowProps) => {
  const {groupName, assetCount, expanded, height, start, canToggle, onToggle} = props;
  return (
    <Row
      className={clsx(
        styles.clickableRow,
        !expanded && styles.clickableRowCollapsed,
        !canToggle && styles.notToggleable,
      )}
      $height={height}
      $start={start}
      onClick={() => canToggle && onToggle(groupName)}
      tabIndex={0}
      onKeyDown={(e) => {
        if (canToggle && (e.code === 'Space' || e.code === 'Enter')) {
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
          {canToggle && <Icon name="arrow_drop_down" size={20} />}
        </Box>
      </Box>
    </Row>
  );
};
