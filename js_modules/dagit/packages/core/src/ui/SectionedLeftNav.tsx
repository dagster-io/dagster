import {BaseTag, Box, Colors, Icon, IconWrapper, StyledTag} from '@dagster-io/ui';
import * as React from 'react';
import {useRouteMatch} from 'react-router-dom';
import styled from 'styled-components/macro';

import {AppContext} from '../app/AppContext';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {useStateWithStorage} from '../hooks/useStateWithStorage';
import {LeftNavItem} from '../nav/LeftNavItem';
import {LeftNavItemType} from '../nav/LeftNavItemType';
import {getAssetGroupItemsForOption, getJobItemsForOption} from '../nav/getLeftNavItemsForOption';
import {explorerPathFromString} from '../pipelines/PipelinePathUtils';
import {DagsterRepoOption, WorkspaceContext} from '../workspace/WorkspaceContext';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {repoAddressAsString} from '../workspace/repoAddressAsString';
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
      const key = repoAddressAsString(repoAddress);
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
    const alphaSorted = [...visibleRepos].sort((a, b) =>
      a.repository.name.toLocaleLowerCase().localeCompare(b.repository.name.toLocaleLowerCase()),
    );
    const reposWithJobs = [];
    const reposWithoutJobs = [];
    for (const repo of alphaSorted) {
      const jobs = repo.repository.pipelines;
      if (jobs.length > 0 && jobs.some((job) => !isHiddenAssetGroupJob(job.name))) {
        reposWithJobs.push(repo);
      } else {
        reposWithoutJobs.push(repo);
      }
    }
    return [...reposWithJobs, ...reposWithoutJobs];
  }, [visibleRepos]);

  if (loading) {
    return <div style={{flex: 1}} />;
  }

  return (
    <>
      <Box
        flex={{direction: 'row', alignItems: 'center', gap: 8}}
        padding={{horizontal: 24, bottom: 12}}
        border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
      >
        <span style={{fontSize: '16px', fontWeight: 500}}>Workspace</span>
      </Box>
      <Container>
        {sortedRepos.map((repo) => {
          const repoName = repo.repository.name;
          const repoAddress = buildRepoAddress(repoName, repo.repositoryLocation.name);
          const addressAsString = repoAddressAsString(repoAddress);
          return (
            <Section
              key={addressAsString}
              onToggle={onToggle}
              option={repo}
              repoAddress={repoAddress}
              expanded={sortedRepos.length === 1 || expandedKeys.includes(addressAsString)}
              collapsible={sortedRepos.length > 1}
              showRepoLocation={duplicateRepoNames.has(repoName)}
              match={match?.repoAddress === repoAddress ? match : null}
            />
          );
        })}
      </Container>
    </>
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
  match: {itemName: string; itemType: 'asset-group' | 'job'} | null;
  repoAddress: RepoAddress;
  showRepoLocation: boolean;
}

export const Section: React.FC<SectionProps> = React.memo((props) => {
  const {expanded, collapsible, onToggle, option, match, repoAddress, showRepoLocation} = props;
  const matchRef = React.useRef<HTMLDivElement>(null);

  const jobItems = React.useMemo(() => getJobItemsForOption(option), [option]);
  const assetGroupItems = React.useMemo(() => getAssetGroupItemsForOption(option), [option]);
  const empty = jobItems.length === 0 && assetGroupItems.length === 0;
  const showTypeLabels = expanded && jobItems.length > 0 && assetGroupItems.length > 0;

  React.useEffect(() => {
    if (match && matchRef.current) {
      matchRef.current.scrollIntoView({block: 'nearest'});
    }
  }, [match]);

  const visibleItems = ({items, type}: {items: LeftNavItemType[]; type: 'job' | 'asset-group'}) => {
    const matchItem =
      match?.itemType === type ? items.find((i) => i.name === match.itemName) : null;

    const shownItems = expanded ? items : matchItem ? [matchItem] : [];
    if (!shownItems.length) {
      return null;
    }

    return (
      <Box padding={{vertical: 8, horizontal: 12}}>
        {showTypeLabels && (
          <ItemTypeLabel>{type === 'asset-group' ? 'Asset Groups' : 'Jobs'}</ItemTypeLabel>
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
            <Box flex={{direction: 'column'}} style={{flex: 1, minWidth: 0}}>
              <RepoName style={{fontWeight: 500}} data-tooltip={option.repository.name}>
                {option.repository.name}
              </RepoName>
              {showRepoLocation ? (
                <RepoLocation data-tooltip={`@${option.repositoryLocation.name}`} $disabled={empty}>
                  @{option.repositoryLocation.name}
                </RepoLocation>
              ) : null}
            </Box>

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
    </Box>
  );
});

type PathMatch = {
  repoPath: string;
  pipelinePath?: string;
  groupName?: string;
};

const usePathMatch = () => {
  const match = useRouteMatch<PathMatch>([
    '/workspace/:repoPath/(jobs|pipelines)/:pipelinePath',
    '/workspace/:repoPath/asset-groups/:groupName',
  ]);
  const {groupName, repoPath, pipelinePath} = match?.params || {};

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
      : null;
  }, [groupName, repoPath, pipelinePath]);
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
  gap: 12px;
  padding: 0 12px 0 24px;
  text-align: left;
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
  text-overflow: ellipsis;
  white-space: nowrap;
`;

const RepoLocation = styled.div<{$disabled: boolean}>`
  color: ${({$disabled}) => ($disabled ? Colors.Gray400 : Colors.Gray700)};
  font-size: 12px;
  margin-top: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
`;
