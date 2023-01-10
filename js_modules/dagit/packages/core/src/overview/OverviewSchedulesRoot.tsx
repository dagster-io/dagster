import {useQuery} from '@apollo/client';
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

import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {useQueryRefreshAtInterval, FIFTEEN_SECONDS} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {graphql} from '../graphql';
import {OverviewSchedulesQueryQuery} from '../graphql/graphql';
import {RepoFilterButton} from '../instance/RepoFilterButton';
import {UnloadableSchedules} from '../instigation/Unloadable';
import {SchedulerInfo} from '../schedules/SchedulerInfo';
import {WorkspaceContext} from '../workspace/WorkspaceContext';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

import {OverviewScheduleTable} from './OverviewSchedulesTable';
import {OverviewTabs} from './OverviewTabs';
import {sortRepoBuckets} from './sortRepoBuckets';
import {visibleRepoKeys} from './visibleRepoKeys';

export const OverviewSchedulesRoot = () => {
  useTrackPageView();

  const [searchValue, setSearchValue] = React.useState('');
  const {allRepos, visibleRepos} = React.useContext(WorkspaceContext);
  const repoCount = allRepos.length;

  const queryResultOverview = useQuery(OVERVIEW_SCHEDULES_QUERY, {
    fetchPolicy: 'network-only',
    notifyOnNetworkStatusChange: true,
  });
  const {data, loading} = queryResultOverview;

  const refreshState = useQueryRefreshAtInterval(queryResultOverview, FIFTEEN_SECONDS);

  const repoBuckets = React.useMemo(() => {
    const visibleKeys = visibleRepoKeys(visibleRepos);
    return buildBuckets(data).filter(({repoAddress}) =>
      visibleKeys.has(repoAddressAsHumanString(repoAddress)),
    );
  }, [data, visibleRepos]);

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

    const anyReposHidden = allRepos.length > visibleRepos.length;

    if (!filteredBySearch.length) {
      if (anySearch) {
        return (
          <Box padding={{top: 20}}>
            <NonIdealState
              icon="search"
              title="No matching schedules"
              description={
                anyReposHidden ? (
                  <div>
                    No schedules matching <strong>{searchValue}</strong> were found in the selected
                    code locations
                  </div>
                ) : (
                  <div>
                    No schedules matching <strong>{searchValue}</strong> were found in your
                    definitions
                  </div>
                )
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
            description={
              anyReposHidden
                ? 'No schedules were found in the selected code locations'
                : 'No schedules were found in your definitions'
            }
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
          <Box
            padding={{vertical: 16, horizontal: 24}}
            border={{side: 'top', width: 1, color: Colors.KeylineGray}}
          >
            <SchedulerInfo daemonHealth={data?.instance.daemonHealth} />
          </Box>
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
                code locations that no longer exist. You can turn them off, but you cannot turn them
                back on.
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
  const {data} = useQuery(UNLOADABLE_SCHEDULES_QUERY);
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

const buildBuckets = (data?: OverviewSchedulesQueryQuery): RepoBucket[] => {
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

  return sortRepoBuckets(buckets);
};

const OVERVIEW_SCHEDULES_QUERY = graphql(`
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
    instance {
      ...InstanceHealthFragment
    }
  }
`);

const UNLOADABLE_SCHEDULES_QUERY = graphql(`
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
`);
