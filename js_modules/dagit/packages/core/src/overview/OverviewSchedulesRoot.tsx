import {gql, useQuery} from '@apollo/client';
import {
  Alert,
  Box,
  Button,
  Colors,
  Dialog,
  DialogFooter,
  Heading,
  NonIdealState,
  PageHeader,
  Spinner,
  TextInput,
} from '@dagster-io/ui';
import * as React from 'react';

import {PythonErrorInfo, PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {useQueryRefreshAtInterval, FIFTEEN_SECONDS} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {RepoFilterButton} from '../instance/RepoFilterButton';
import {INSTIGATION_STATE_FRAGMENT} from '../instigation/InstigationUtils';
import {UnloadableSchedules} from '../instigation/Unloadable';
import {WorkspaceContext} from '../workspace/WorkspaceContext';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {RepoAddress} from '../workspace/types';

import {OverviewScheduleTable} from './OverviewSchedulesTable';
import {OverviewTabs} from './OverviewTabs';
import {OverviewSchedulesQuery} from './types/OverviewSchedulesQuery';
import {UnloadableSchedulesQuery} from './types/UnloadableSchedulesQuery';

export const OverviewSchedulesRoot = () => {
  useTrackPageView();

  const [searchValue, setSearchValue] = React.useState('');
  const {allRepos} = React.useContext(WorkspaceContext);
  const repoCount = allRepos.length;

  const queryResultOverview = useQuery<OverviewSchedulesQuery>(OVERVIEW_SCHEDULES_QUERY, {
    fetchPolicy: 'network-only',
    notifyOnNetworkStatusChange: true,
  });
  const {data, loading} = queryResultOverview;

  const refreshState = useQueryRefreshAtInterval(queryResultOverview, FIFTEEN_SECONDS);

  const repoBuckets = useRepoBuckets(data);
  const sanitizedSearch = searchValue.trim().toLocaleLowerCase();
  const anySearch = sanitizedSearch.length > 0;

  const filteredBySearch = React.useMemo(() => {
    const searchToLower = sanitizedSearch.toLocaleLowerCase();
    return repoBuckets
      .map(({repoAddress, schedules}) => ({
        repoAddress,
        schedules: schedules.filter((name) => name.toLocaleLowerCase().includes(searchToLower)),
      }))
      .filter(({schedules}) => schedules.length > 0);
  }, [repoBuckets, sanitizedSearch]);

  const content = () => {
    if (loading && !data) {
      return (
        <Box flex={{direction: 'row', justifyContent: 'center'}} style={{paddingTop: '100px'}}>
          <Box flex={{direction: 'row', alignItems: 'center', gap: 16}}>
            <Spinner purpose="body-text" />
            <div style={{color: Colors.Gray600}}>Loading schedules…</div>
          </Box>
        </Box>
      );
    }

    if (!filteredBySearch.length) {
      if (anySearch) {
        return (
          <Box padding={{top: 20}}>
            <NonIdealState
              icon="search"
              title="No matching schedules"
              description={
                <div>
                  No schedules matching <strong>{searchValue}</strong> were found in this workspace
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
            title="No schedules"
            description="No schedules were found in this workspace"
          />
        </Box>
      );
    }

    return <OverviewScheduleTable repos={filteredBySearch} />;
  };

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
      <PageHeader
        title={<Heading>Overview</Heading>}
        tabs={<OverviewTabs tab="schedules" refreshState={refreshState} />}
      />
      <Box
        padding={{horizontal: 24, vertical: 16}}
        flex={{direction: 'row', alignItems: 'center', gap: 12, grow: 0}}
      >
        {repoCount > 0 ? <RepoFilterButton /> : null}
        <TextInput
          icon="search"
          value={searchValue}
          onChange={(e) => setSearchValue(e.target.value)}
          placeholder="Filter by schedule name…"
          style={{width: '340px'}}
        />
      </Box>
      {loading && !repoCount ? (
        <Box padding={64}>
          <Spinner purpose="page" />
        </Box>
      ) : (
        <>
          {data?.unloadableInstigationStatesOrError.__typename === 'InstigationStates' ? (
            <UnloadableSchedulesAlert
              count={data.unloadableInstigationStatesOrError.results.length}
            />
          ) : null}
          {content()}
        </>
      )}
    </Box>
  );
};

const UnloadableSchedulesAlert: React.FC<{
  count: number;
}> = ({count}) => {
  const [isOpen, setIsOpen] = React.useState(false);

  if (!count) {
    return null;
  }

  const title = count === 1 ? '1 unloadable schedule' : `${count} unloadable schedules`;

  return (
    <>
      <Box
        padding={{vertical: 16, horizontal: 24}}
        border={{side: 'top', width: 1, color: Colors.KeylineGray}}
      >
        <Alert
          intent="warning"
          title={title}
          description={
            <Box flex={{direction: 'column', gap: 12, alignItems: 'flex-start'}}>
              <div>
                Schedules were previously started but now cannot be loaded. They may be part of a
                different workspace or from a schedule or repository that no longer exists in code.
                You can turn them off, but you cannot turn them back on.
              </div>
              <Button onClick={() => setIsOpen(true)}>
                {count === 1 ? 'View unloadable schedule' : 'View unloadable schedules'}
              </Button>
            </Box>
          }
        />
      </Box>
      <Dialog
        isOpen={isOpen}
        title="Unloadable schedules"
        style={{width: '90vw', maxWidth: '1200px'}}
      >
        <Box padding={{bottom: 8}}>
          <UnloadableScheduleDialog />
        </Box>
        <DialogFooter>
          <Button intent="primary" onClick={() => setIsOpen(false)}>
            Done
          </Button>
        </DialogFooter>
      </Dialog>
    </>
  );
};

const UnloadableScheduleDialog: React.FC = () => {
  const {data} = useQuery<UnloadableSchedulesQuery>(UNLOADABLE_SCHEDULES_QUERY);
  if (!data) {
    return <Spinner purpose="section" />;
  }

  if (data?.unloadableInstigationStatesOrError.__typename === 'InstigationStates') {
    return (
      <UnloadableSchedules
        scheduleStates={data.unloadableInstigationStatesOrError.results}
        showSubheading={false}
      />
    );
  }

  return <PythonErrorInfo error={data?.unloadableInstigationStatesOrError} />;
};

type RepoBucket = {
  repoAddress: RepoAddress;
  schedules: string[];
};

const useRepoBuckets = (data?: OverviewSchedulesQuery): RepoBucket[] => {
  return React.useMemo(() => {
    if (data?.workspaceOrError.__typename !== 'Workspace') {
      return [];
    }

    const entries = data.workspaceOrError.locationEntries.map((entry) => entry.locationOrLoadError);

    const buckets = [];

    for (const entry of entries) {
      if (entry?.__typename !== 'RepositoryLocation') {
        continue;
      }

      for (const repo of entry.repositories) {
        const {name, schedules} = repo;
        const repoAddress = buildRepoAddress(name, entry.name);
        const scheduleNames = schedules.map(({name}) => name);

        if (scheduleNames.length > 0) {
          buckets.push({
            repoAddress,
            schedules: scheduleNames,
          });
        }
      }
    }

    return buckets;
  }, [data]);
};

const OVERVIEW_SCHEDULES_QUERY = gql`
  query OverviewSchedulesQuery {
    workspaceOrError {
      ... on Workspace {
        locationEntries {
          id
          locationOrLoadError {
            ... on RepositoryLocation {
              id
              name
              repositories {
                id
                name
                schedules {
                  id
                  name
                  description
                }
              }
            }
            ...PythonErrorFragment
          }
        }
      }
      ...PythonErrorFragment
    }
    unloadableInstigationStatesOrError(instigationType: SCHEDULE) {
      ... on InstigationStates {
        results {
          id
        }
      }
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
`;

const UNLOADABLE_SCHEDULES_QUERY = gql`
  query UnloadableSchedulesQuery {
    unloadableInstigationStatesOrError(instigationType: SCHEDULE) {
      ... on InstigationStates {
        results {
          id
          ...InstigationStateFragment
        }
      }
      ...PythonErrorFragment
    }
  }

  ${INSTIGATION_STATE_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;
