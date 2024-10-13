import {
  BaseTag,
  Box,
  Colors,
  Icon,
  IconWrapper,
  MiddleTruncate,
  StyledTag,
} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';
import {useRouteMatch} from 'react-router-dom';
import styled from 'styled-components';

import {Inner, Row} from './VirtualizedTable';
import {AppContext} from '../app/AppContext';
import {useFeatureFlags} from '../app/Flags';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {useStateWithStorage} from '../hooks/useStateWithStorage';
import {LeftNavItem} from '../nav/LeftNavItem';
import {LeftNavItemType} from '../nav/LeftNavItemType';
import {
  getAssetGroupItemsForOption,
  getJobItemsForOption,
  getTopLevelResourceDetailsItemsForOption,
} from '../nav/getLeftNavItemsForOption';
import {explorerPathFromString} from '../pipelines/PipelinePathUtils';
import {WorkspaceContext} from '../workspace/WorkspaceContext/WorkspaceContext';
import {DUNDER_REPO_NAME, buildRepoAddress} from '../workspace/buildRepoAddress';
import {repoAddressAsHumanString, repoAddressAsURLString} from '../workspace/repoAddressAsString';
import {repoAddressFromPath} from '../workspace/repoAddressFromPath';
import {RepoAddress} from '../workspace/types';

const validateExpandedKeys = (parsed: unknown) => (Array.isArray(parsed) ? parsed : []);
const EXPANDED_REPO_KEYS = 'dagster.expanded-repo-keys';

type ItemType = 'asset-group' | 'job' | 'resource';

type RowType =
  | {type: 'code-location'; repoAddress: RepoAddress; itemCount: number}
  | {type: 'item-type'; itemType: ItemType; isFirst: boolean}
  | {
      type: 'item';
      repoAddress: RepoAddress;
      item: LeftNavItemType;
      itemType: ItemType;
      isFirst: boolean;
      isLast: boolean;
    };

export const SectionedLeftNav = () => {
  const {visibleRepos} = React.useContext(WorkspaceContext);
  const {basePath} = React.useContext(AppContext);
  const parentRef = React.useRef<HTMLDivElement | null>(null);

  const {flagSidebarResources} = useFeatureFlags();
  const match = usePathMatch();

  const [expandedKeys, setExpandedKeys] = useStateWithStorage<string[]>(
    basePath + ':' + EXPANDED_REPO_KEYS,
    validateExpandedKeys,
  );

  const onToggle = React.useCallback(
    (repoAddress: RepoAddress) => {
      const key = repoAddressAsURLString(repoAddress);
      setExpandedKeys((current) => {
        let nextExpandedKeys = [...(current || [])];
        if (nextExpandedKeys.includes(key)) {
          nextExpandedKeys = nextExpandedKeys.filter((k) => k !== key);
        } else {
          nextExpandedKeys = [...nextExpandedKeys, key];
        }
        return nextExpandedKeys;
      });
    },
    [setExpandedKeys],
  );

  const visibleReposAndKeys = React.useMemo(() => {
    return visibleRepos.map((repo) => {
      const repoAddress = buildRepoAddress(repo.repository.name, repo.repositoryLocation.name);
      return {
        repo,
        repoAddress,
        key: repoAddressAsURLString(repoAddress),
        label: repoAddressAsHumanString(repoAddress),
        jobItems: getJobItemsForOption(repo),
        assetGroupItems: getAssetGroupItemsForOption(repo),
        resourceItems: flagSidebarResources ? getTopLevelResourceDetailsItemsForOption(repo) : [],
      };
    });
  }, [flagSidebarResources, visibleRepos]);

  const duplicateRepoNames = React.useMemo(() => {
    const uniques = new Set<string>();
    const duplicates = new Set<string>();
    visibleRepos.forEach((repo) => {
      const repoName = repo.repository.name;
      if (uniques.has(repoName)) {
        duplicates.add(repoName);
      } else {
        uniques.add(repoName);
      }
    });
    return duplicates;
  }, [visibleRepos]);

  // Sort repositories alphabetically, then move empty repos to the bottom.
  const sortedRepos = React.useMemo(() => {
    const alphaSorted = [...visibleReposAndKeys].sort((a, b) =>
      a.label.toLocaleLowerCase().localeCompare(b.label.toLocaleLowerCase()),
    );
    const reposWithJobs = [];
    const reposWithoutJobs = [];
    for (const repoWithKey of alphaSorted) {
      const jobs = repoWithKey.repo.repository.pipelines;
      if (jobs.length > 0 && jobs.some((job) => !isHiddenAssetGroupJob(job.name))) {
        reposWithJobs.push(repoWithKey);
      } else {
        reposWithoutJobs.push(repoWithKey);
      }
    }
    return [...reposWithJobs, ...reposWithoutJobs];
  }, [visibleReposAndKeys]);

  const flattened: RowType[] = React.useMemo(() => {
    const flat: RowType[] = [];
    for (const repoWithKey of sortedRepos) {
      const {repoAddress, key, jobItems, assetGroupItems, resourceItems} = repoWithKey;
      if (!repoAddress) {
        continue;
      }

      const jobCount = jobItems.length;
      const assetGroupCount = assetGroupItems.length;
      const resourceCount = resourceItems.length;

      const itemCount = jobCount + assetGroupCount + resourceCount;
      const showTypeLabels =
        itemCount > jobCount && itemCount > assetGroupCount && itemCount > resourceCount;

      flat.push({type: 'code-location', repoAddress, itemCount});

      if (expandedKeys.includes(key) || sortedRepos.length === 1) {
        if (jobItems.length) {
          if (showTypeLabels) {
            flat.push({type: 'item-type', itemType: 'job', isFirst: true});
          }
          jobItems.forEach((item, ii) => {
            flat.push({
              type: 'item',
              repoAddress,
              itemType: 'job',
              item,
              isFirst: !showTypeLabels && ii === 0,
              isLast: ii === jobItems.length - 1,
            });
          });
        }

        if (assetGroupItems.length) {
          if (showTypeLabels) {
            flat.push({type: 'item-type', itemType: 'asset-group', isFirst: !jobCount});
          }
          assetGroupItems.forEach((item, ii) => {
            flat.push({
              type: 'item',
              repoAddress,
              itemType: 'asset-group',
              item,
              isFirst: !showTypeLabels && ii === 0,
              isLast: ii === assetGroupItems.length - 1,
            });
          });
        }

        if (resourceItems.length) {
          if (showTypeLabels) {
            flat.push({
              type: 'item-type',
              itemType: 'resource',
              isFirst: !jobCount && !assetGroupCount,
            });
          }
          resourceItems.forEach((item, ii) => {
            flat.push({
              type: 'item',
              repoAddress,
              itemType: 'resource',
              item,
              isFirst: !showTypeLabels && ii === 0,
              isLast: ii === resourceItems.length - 1,
            });
          });
        }
      }
    }

    return flat;
  }, [expandedKeys, sortedRepos]);

  const rowVirtualizer = useVirtualizer({
    count: flattened.length,
    getScrollElement: () => parentRef.current,
    estimateSize: (index: number) => {
      const item = flattened[index]!;
      switch (item.type) {
        case 'code-location':
          return 48;
        case 'item-type':
          return item.isFirst ? 32 : 28;
        case 'item': {
          let height = 30;
          if (item.isFirst) {
            height += 4;
          }
          if (item.isLast) {
            height += 4;
          }
          return height;
        }
      }
    },
    overscan: 10,
  });

  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  const collapsible = sortedRepos.length > 1;

  return (
    <Container ref={parentRef}>
      <Inner $totalHeight={totalHeight}>
        {items.map(({index, key, size, start}) => {
          const row: RowType = flattened[index]!;
          const type = row!.type;

          if (type === 'code-location') {
            const repoAddress = row.repoAddress;
            const addressAsString = repoAddressAsURLString(repoAddress);
            const expanded = sortedRepos.length === 1 || expandedKeys.includes(addressAsString);
            return (
              <CodeLocationNameRow
                key={key}
                height={size}
                start={start}
                repoAddress={repoAddress}
                itemCount={row.itemCount}
                collapsible={collapsible}
                showRepoLocation={
                  duplicateRepoNames.has(addressAsString) && addressAsString !== DUNDER_REPO_NAME
                }
                expanded={expanded}
                onToggle={onToggle}
              />
            );
          }

          if (type === 'item-type') {
            return (
              <ItemTypeLabelRow
                key={key}
                height={size}
                start={start}
                itemType={row.itemType}
                isFirst={row.isFirst}
              />
            );
          }

          const isMatch =
            match?.repoAddress === row.repoAddress &&
            match?.itemType === row.itemType &&
            match?.itemName === row.item.name;

          return (
            <ItemRow
              key={key}
              height={size}
              start={start}
              item={row.item}
              isMatch={isMatch}
              isFirst={row.isFirst}
              isLast={row.isLast}
            />
          );
        })}
      </Inner>
    </Container>
  );
};

const Container = styled.div`
  height: 100%;
  overflow: auto;
  background-color: ${Colors.backgroundLight()};
`;

interface CodeLocationNameRowProps {
  height: number;
  start: number;
  expanded: boolean;
  collapsible: boolean;
  itemCount: number;
  onToggle: (repoAddress: RepoAddress) => void;
  repoAddress: RepoAddress;
  showRepoLocation: boolean;
}

const CodeLocationNameRow = (props: CodeLocationNameRowProps) => {
  const {height, start, expanded, collapsible, onToggle, itemCount, repoAddress, showRepoLocation} =
    props;

  const codeLocationLabel = repoAddressAsHumanString(repoAddress);
  const empty = itemCount === 0;

  return (
    <Row $height={height} $start={start}>
      <SectionHeader
        $open={expanded && !empty}
        $showRepoLocation={showRepoLocation}
        disabled={empty}
        onClick={collapsible ? () => onToggle(repoAddress) : undefined}
      >
        <Box
          flex={{direction: 'row', alignItems: 'flex-start', gap: 8}}
          style={{flex: 1, maxWidth: '100%'}}
        >
          <Box margin={{top: 2}}>
            <Icon name="folder_open" size={16} />
          </Box>
          <RepoNameContainer>
            <RepoName
              data-tooltip={codeLocationLabel}
              data-tooltip-style={CodeLocationTooltipStyles}
            >
              <MiddleTruncate text={codeLocationLabel} showTitle={false} />
            </RepoName>
            {/* Wrapper div to prevent tag from stretching vertically */}
            <div>
              <BaseTag
                fillColor={Colors.backgroundGray()}
                textColor={Colors.textDefault()}
                label={itemCount.toLocaleString()}
              />
            </div>
          </RepoNameContainer>
          {collapsible && (
            <Box margin={{top: 2}}>
              <Icon name="arrow_drop_down" />
            </Box>
          )}
        </Box>
      </SectionHeader>
    </Row>
  );
};

interface ItemTypeLabelRowProps {
  height: number;
  start: number;
  itemType: ItemType;
  isFirst: boolean;
}

const ItemTypeLabelRow = (props: ItemTypeLabelRowProps) => {
  const {height, start, itemType, isFirst} = props;
  const label = React.useMemo(() => {
    switch (itemType) {
      case 'asset-group':
        return 'Asset groups';
      case 'job':
        return 'Jobs';
      case 'resource':
        return 'Resources';
    }
  }, [itemType]);
  return (
    <Row $height={height} $start={start}>
      <Box padding={{top: isFirst ? 12 : 8, horizontal: 12}}>
        <ItemTypeLabel>{label}</ItemTypeLabel>
      </Box>
    </Row>
  );
};

interface ItemRowProps {
  height: number;
  start: number;
  item: LeftNavItemType;
  isMatch: boolean;
  isFirst: boolean;
  isLast: boolean;
}

const ItemRow = (props: ItemRowProps) => {
  const {height, start, item, isMatch, isFirst, isLast} = props;
  const matchRef = React.useRef<HTMLDivElement | null>(null);

  React.useEffect(() => {
    if (isMatch && matchRef.current) {
      matchRef.current.scrollIntoView({block: 'nearest'});
    }
  }, [isMatch]);

  return (
    <Row $height={height} $start={start}>
      <Box padding={{horizontal: 12, top: isFirst ? 4 : 0, bottom: isLast ? 4 : 0}}>
        <LeftNavItem
          item={item}
          key={item.path}
          ref={isMatch ? matchRef : undefined}
          active={isMatch}
        />
      </Box>
    </Row>
  );
};

const CodeLocationTooltipStyles = JSON.stringify({
  background: Colors.backgroundLightHover(),
  filter: `brightness(97%)`,
  color: Colors.textDefault(),
  fontWeight: 500,
  border: 'none',
  borderRadius: 7,
  overflow: 'hidden',
  fontSize: 14,
  padding: '5px 10px',
  transform: 'translate(-10px,-5px)',
} as React.CSSProperties);

type PathMatch = {
  repoPath: string;
  pipelinePath?: string;
  groupName?: string;
  resourceName?: string;
};

const usePathMatch = () => {
  const match = useRouteMatch<PathMatch>([
    '/locations/:repoPath/(jobs|pipelines)/:pipelinePath',
    '/locations/:repoPath/asset-groups/:groupName',
    '/locations/:repoPath/resources/:resourceName',
  ]);
  const {groupName, repoPath, pipelinePath, resourceName} = match?.params || {};

  return React.useMemo(() => {
    if (!repoPath) {
      return null;
    }
    const repoAddress = repoAddressFromPath(repoPath);
    if (!repoAddress) {
      return null;
    }

    return pipelinePath
      ? {
          repoAddress,
          itemName: explorerPathFromString(pipelinePath).pipelineName,
          itemType: 'job' as const,
        }
      : groupName
      ? {
          repoAddress,
          itemName: groupName,
          itemType: 'asset-group' as const,
        }
      : resourceName
      ? {
          repoAddress,
          itemName: resourceName,
          itemType: 'resource' as const,
        }
      : null;
  }, [groupName, repoPath, pipelinePath, resourceName]);
};

const ItemTypeLabel = styled.div`
  color: ${Colors.textLighter()};
  padding: 0 12px 4px;
  font-size: 12px;
`;

const SectionHeader = styled.button<{
  $open: boolean;
  $showRepoLocation: boolean;
}>`
  background: ${Colors.backgroundLight()};
  border: 0;
  border-radius: 0;
  cursor: pointer;
  display: flex;
  align-items: center;
  font-size: 14px;
  gap: 12px;
  padding: 12px 12px 12px 24px;
  text-align: left;
  user-select: none;
  white-space: nowrap;
  transition: background 100ms linear;

  width: 100%;
  margin: 0;

  box-shadow: inset 0px 1px 0 ${Colors.keylineDefault()}, inset 0px -1px 0 ${Colors.keylineDefault()};

  :disabled {
    cursor: default;
  }

  :hover,
  :active {
    background-color: ${Colors.backgroundLightHover()};
  }

  :disabled:hover,
  :disabled:active {
    background-color: ${Colors.backgroundDisabled()};
  }

  :focus,
  :active {
    outline: none;
  }

  ${IconWrapper}[aria-label="arrow_drop_down"] {
    transition: transform 100ms linear;
    ${({$open}) => ($open ? null : `transform: rotate(-90deg);`)}
  }

  :disabled ${IconWrapper} {
    background-color: ${Colors.textDisabled()};
  }

  ${StyledTag} {
    margin-top: -3px;
    margin-left: 6px;
  }

  :not(:disabled) ${StyledTag} {
    cursor: pointer;
  }

  :disabled ${StyledTag} {
    color: ${Colors.textDisabled()};
  }
}`;

const RepoNameContainer = styled.div`
  display: flex;
  justify-content: space-between;
  margin-top: 2px;
  flex: 1;
  min-width: 0;
`;

const RepoName = styled.div`
  font-weight: 500;
  overflow: hidden;
  white-space: nowrap;
`;
