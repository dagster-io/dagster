import {BaseTag, Box, Colors, Icon, IconWrapper, MiddleTruncate, StyledTag} from '@dagster-io/ui';
import * as React from 'react';
import {useRouteMatch} from 'react-router-dom';
import styled from 'styled-components/macro';

import {AppContext} from '../app/AppContext';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {useStateWithStorage} from '../hooks/useStateWithStorage';
import {LeftNavItem} from '../nav/LeftNavItem';
import {LeftNavItemType} from '../nav/LeftNavItemType';
import {
  getAssetGroupItemsForOption,
  getJobItemsForOption,
  getTopLevelResourceItemsForOption,
} from '../nav/getLeftNavItemsForOption';
import {explorerPathFromString} from '../pipelines/PipelinePathUtils';
import {DagsterRepoOption, WorkspaceContext} from '../workspace/WorkspaceContext';
import {buildRepoAddress, DUNDER_REPO_NAME} from '../workspace/buildRepoAddress';
import {repoAddressAsHumanString, repoAddressAsURLString} from '../workspace/repoAddressAsString';
import {repoAddressFromPath} from '../workspace/repoAddressFromPath';
import {RepoAddress} from '../workspace/types';

const validateExpandedKeys = (parsed: unknown) => (Array.isArray(parsed) ? parsed : []);
const EXPANDED_REPO_KEYS = 'dagit.expanded-repo-keys';

export const SectionedLeftNav = () => {
  const {loading, visibleRepos} = React.useContext(WorkspaceContext);
  const {basePath} = React.useContext(AppContext);

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
        key: repoAddressAsHumanString(repoAddress),
      };
    });
  }, [visibleRepos]);

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
      a.key.toLocaleLowerCase().localeCompare(b.key.toLocaleLowerCase()),
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

  if (loading) {
    return <div style={{flex: 1}} />;
  }

  return (
    <Container>
      {sortedRepos.map(({repo, repoAddress, key}) => {
        const {name} = repoAddress;
        const addressAsString = repoAddressAsURLString(repoAddress);
        return (
          <Section
            key={key}
            onToggle={onToggle}
            option={repo}
            repoAddress={repoAddress}
            expanded={sortedRepos.length === 1 || expandedKeys.includes(addressAsString)}
            collapsible={sortedRepos.length > 1}
            showRepoLocation={duplicateRepoNames.has(name) && name !== DUNDER_REPO_NAME}
            match={match?.repoAddress === repoAddress ? match : null}
          />
        );
      })}
    </Container>
  );
};

const HEADER_HEIGHT = 48;
const HEADER_HEIGHT_WITH_LOCATION = 64;

// Note: This component uses React.memo so that it only re-renders when it's props change.
// This means opening/closing a collapsed section doesn't re-render other sections (a nice
// perf win) but more importantly opening a section doesn't cause the view to scroll back
// to the selected item, which could be offscreen.
//
interface SectionProps {
  expanded: boolean;
  collapsible: boolean;
  onToggle: (repoAddress: RepoAddress) => void;
  option: DagsterRepoOption;
  match: {itemName: string; itemType: 'asset-group' | 'job' | 'resource'} | null;
  repoAddress: RepoAddress;
  showRepoLocation: boolean;
}

export const Section: React.FC<SectionProps> = React.memo((props) => {
  const {expanded, collapsible, onToggle, option, match, repoAddress, showRepoLocation} = props;
  const matchRef = React.useRef<HTMLDivElement>(null);

  const jobItems = React.useMemo(() => getJobItemsForOption(option), [option]);
  const assetGroupItems = React.useMemo(() => getAssetGroupItemsForOption(option), [option]);
  const resourceItems = React.useMemo(() => getTopLevelResourceItemsForOption(option), [option]);
  const empty = jobItems.length === 0 && assetGroupItems.length === 0 && resourceItems.length === 0;
  const showTypeLabels =
    expanded &&
    [jobItems.length > 0, assetGroupItems.length > 0, resourceItems.length > 0].filter(Boolean)
      .length > 1;

  React.useEffect(() => {
    if (match && matchRef.current) {
      matchRef.current.scrollIntoView({block: 'nearest'});
    }
  }, [match]);

  const visibleItems = ({
    items,
    type,
  }: {
    items: LeftNavItemType[];
    type: 'job' | 'asset-group' | 'resource';
  }) => {
    const matchItem =
      match?.itemType === type ? items.find((i) => i.name === match.itemName) : null;

    const shownItems = expanded ? items : matchItem ? [matchItem] : [];
    if (!shownItems.length) {
      return null;
    }

    return (
      <Box padding={{vertical: 8, horizontal: 12}}>
        {showTypeLabels && (
          <ItemTypeLabel>
            {type === 'asset-group' ? 'Asset Groups' : type === 'resource' ? 'Resources' : 'Jobs'}
          </ItemTypeLabel>
        )}
        {shownItems.map((item) => (
          <LeftNavItem
            item={item}
            key={item.path}
            ref={item === matchItem ? matchRef : undefined}
            active={item === matchItem}
          />
        ))}
      </Box>
    );
  };

  return (
    <Box background={Colors.Gray100} border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}>
      <SectionHeader
        $open={expanded && !empty}
        $showTypeLabels={showTypeLabels}
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
              data-tooltip={repoAddressAsHumanString(repoAddress)}
              data-tooltip-style={CodeLocationTooltipStyles}
            >
              <MiddleTruncate text={repoAddressAsHumanString(repoAddress)} showTitle={false} />
            </RepoName>
            {/* Wrapper div to prevent tag from stretching vertically */}
            <div>
              <BaseTag
                fillColor={Colors.Gray10}
                textColor={Colors.Dark}
                label={(jobItems.length + assetGroupItems.length).toLocaleString()}
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
      {visibleItems({type: 'job', items: jobItems})}
      {visibleItems({type: 'asset-group', items: assetGroupItems})}
      {visibleItems({type: 'resource', items: resourceItems})}
    </Box>
  );
});

const CodeLocationTooltipStyles = JSON.stringify({
  background: Colors.Gray100,
  filter: `brightness(97%)`,
  color: Colors.Gray900,
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
  color: ${Colors.Gray600};
  padding: 0 12px 4px;
  font-size: 12px;
`;

const Container = styled.div`
  background-color: ${Colors.Gray100};
  overflow-y: auto;
  overflow-x: hidden;
`;

const SectionHeader = styled.button<{
  $open: boolean;
  $showTypeLabels: boolean;
  $showRepoLocation: boolean;
}>`
  background: ${Colors.Gray100};
  border: 0;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  font-size: 14px;
  gap: 12px;
  padding: 0 12px 0 24px;
  text-align: left;
  user-select: none;
  white-space: nowrap;

  height: ${({$showRepoLocation}) =>
    $showRepoLocation ? HEADER_HEIGHT_WITH_LOCATION : HEADER_HEIGHT}px;
  width: 100%;
  margin: 0;
  margin-bottom: ${({$showTypeLabels}) => ($showTypeLabels ? '8px' : 0)};
  
  box-shadow: inset 0px -1px 0 ${Colors.KeylineGray};

  :disabled {
    cursor: default;
  }

  :hover,
  :active {
    background-color: ${Colors.Gray50};
  }

  :disabled:hover,
  :disabled:active {
    background-color: ${Colors.Gray100};
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
    background-color: ${Colors.Gray300};
  }

  ${StyledTag} {
    margin-top: -3px;
    margin-left: 6px;
  }

  :not(:disabled) ${StyledTag} {
    cursor: pointer;
  }

  :disabled ${StyledTag} {
    color: ${Colors.Gray400};
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
