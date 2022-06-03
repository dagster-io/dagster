import {BaseTag, Box, Colors, Icon, IconWrapper, StyledTag} from '@dagster-io/ui';
import * as React from 'react';
import {useRouteMatch} from 'react-router-dom';
import styled from 'styled-components/macro';

import {AppContext} from '../app/AppContext';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {useStateWithStorage} from '../hooks/useStateWithStorage';
import {getLeftNavItemsForOption, LeftNavItem} from '../nav/FlatContentList';
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

  const jobMatch = usePathMatch();

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
        <Icon name="job" />
        <span style={{fontSize: '16px', fontWeight: 600}}>Jobs</span>
      </Box>
      <Container>
        {sortedRepos.map((repo) => {
          const repoName = repo.repository.name;
          const repoAddress = buildRepoAddress(repoName, repo.repositoryLocation.name);
          const addressAsString = repoAddressAsString(repoAddress);
          const pathMatch = jobMatch?.repoAddress === repoAddress ? jobMatch.jobName : null;
          return (
            <Section
              key={addressAsString}
              onToggle={onToggle}
              option={repo}
              repoAddress={repoAddress}
              expanded={expandedKeys.includes(addressAsString)}
              showRepoLocation={duplicateRepoNames.has(repoName)}
              pathJobMatch={pathMatch}
            />
          );
        })}
      </Container>
    </>
  );
};

const HEADER_HEIGHT = 48;
const HEADER_HEIGHT_WITH_LOCATION = 64;

interface SectionProps {
  expanded: boolean;
  onToggle: (repoAddress: RepoAddress) => void;
  option: DagsterRepoOption;
  pathJobMatch: string | null;
  repoAddress: RepoAddress;
  showRepoLocation: boolean;
}

export const Section: React.FC<SectionProps> = (props) => {
  const {expanded, onToggle, option, pathJobMatch, repoAddress, showRepoLocation} = props;
  const jobItems = React.useMemo(() => getLeftNavItemsForOption(option), [option]);

  const anyJobs = jobItems.length > 0;
  const showJobs = expanded && anyJobs;
  const match = pathJobMatch && jobItems.find((job) => job.name === pathJobMatch);
  const matchRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (match && matchRef.current) {
      matchRef.current.scrollIntoView({block: 'nearest'});
    }
  }, [match]);

  const visibleJobs = () => {
    if (showJobs) {
      return (
        <Box
          padding={{vertical: 8, horizontal: 12}}
          border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
        >
          {jobItems.map((jobItem) => {
            const active = pathJobMatch === jobItem.name;
            return (
              <LeftNavItem
                job={jobItem}
                key={jobItem.path}
                ref={active ? matchRef : undefined}
                active={active}
              />
            );
          })}
        </Box>
      );
    }

    if (match) {
      return (
        <Box
          padding={{vertical: 8, horizontal: 12}}
          border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
        >
          <LeftNavItem job={match} active ref={matchRef} />
        </Box>
      );
    }

    return null;
  };

  return (
    <Box background={Colors.Gray100}>
      <SectionHeader
        $open={showJobs}
        $showRepoLocation={showRepoLocation}
        disabled={!anyJobs}
        onClick={() => onToggle(repoAddress)}
      >
        <Box flex={{direction: 'row', alignItems: 'flex-start', gap: 8}}>
          <Box margin={{top: 2}}>
            <Icon name="folder_open" size={16} />
          </Box>
          <RepoNameContainer>
            <div style={{minWidth: 0}}>
              <RepoName style={{fontWeight: 500}} data-tooltip={option.repository.name}>
                {option.repository.name}
              </RepoName>
              {showRepoLocation ? (
                <RepoLocation
                  data-tooltip={`@${option.repositoryLocation.name}`}
                  $disabled={!anyJobs}
                >
                  @{option.repositoryLocation.name}
                </RepoLocation>
              ) : null}
            </div>
            {/* Wrapper div to prevent tag from stretching vertically */}
            <div>
              <BaseTag
                fillColor={Colors.Gray10}
                textColor={Colors.Dark}
                label={jobItems.length.toLocaleString()}
              />
            </div>
          </RepoNameContainer>
          <Box margin={{top: 2}}>
            <Icon name="arrow_drop_down" />
          </Box>
        </Box>
      </SectionHeader>
      {visibleJobs()}
    </Box>
  );
};

type PathMatch = {
  repoPath: string;
  pipelinePath: string;
};

const usePathMatch = () => {
  const jobMatch = useRouteMatch<PathMatch>('/workspace/:repoPath/jobs/:pipelinePath');
  const pipelineMatch = useRouteMatch<PathMatch>('/workspace/:repoPath/pipelines/:pipelinePath');

  const jobMatchParams = jobMatch?.params;
  const pipelineMatchParams = pipelineMatch?.params;

  const match = jobMatchParams || pipelineMatchParams;
  const repoPath = match?.repoPath;
  const jobPath = match?.pipelinePath;

  if (repoPath && jobPath) {
    const repoAddress = repoAddressFromPath(repoPath);
    const explorerPath = explorerPathFromString(jobPath);
    const jobName = explorerPath.pipelineName;
    if (repoAddress && jobName) {
      return {repoAddress, jobName};
    }
  }

  return null;
};

const Container = styled.div`
  background-color: ${Colors.Gray100};
  overflow-y: auto;
  overflow-x: hidden;
`;

const SectionHeader = styled.button<{$open: boolean; $showRepoLocation: boolean}>`
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
  width: 244px;
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
