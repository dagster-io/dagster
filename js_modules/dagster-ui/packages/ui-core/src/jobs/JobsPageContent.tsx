import {
  Box,
  Colors,
  Icon,
  NonIdealState,
  Spinner,
  SpinnerWithText,
} from '@dagster-io/ui-components';
import {useCallback, useContext, useMemo} from 'react';

import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {useQueryPersistedFilterState} from '../hooks/useQueryPersistedFilterState';
import {TruncatedTextWithFullTextOnHover} from '../nav/getLeftNavItemsForOption';
import {OverviewJobsTable} from '../overview/OverviewJobsTable';
import {sortRepoBuckets} from '../overview/sortRepoBuckets';
import {visibleRepoKeys} from '../overview/visibleRepoKeys';
import {useFilters} from '../ui/BaseFilters/useFilters';
import {useStaticSetFilter} from '../ui/BaseFilters/useStaticSetFilter';
import {useCodeLocationFilter} from '../ui/Filters/useCodeLocationFilter';
import {Tag} from '../ui/Filters/useDefinitionTagFilter';
import {WorkspaceContext} from '../workspace/WorkspaceContext/WorkspaceContext';
import {
  WorkspaceLocationNodeFragment,
  WorkspacePipelineFragment,
} from '../workspace/WorkspaceContext/types/WorkspaceQueries.types';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

const FILTER_FIELDS = ['jobs', 'tags', 'codeLocations'] as const;

export const JobsPageContent = () => {
  const {allRepos, visibleRepos, loading, data: cachedData} = useContext(WorkspaceContext);
  const repoCount = allRepos.length;
  // Batch up the data and bucket by repo.
  const repoBuckets = useMemo(() => {
    const cachedEntries = Object.values(cachedData).filter(
      (location): location is Extract<typeof location, {__typename: 'WorkspaceLocationEntry'}> =>
        location.__typename === 'WorkspaceLocationEntry',
    );
    const visibleKeys = visibleRepoKeys(visibleRepos);
    return buildBuckets(cachedEntries).filter(({repoAddress}) =>
      visibleKeys.has(repoAddressAsHumanString(repoAddress)),
    );
  }, [cachedData, visibleRepos]);

  const allJobs = useMemo(() => repoBuckets.flatMap((bucket) => bucket.jobs), [repoBuckets]);

  const {state: _state, setters} = useQueryPersistedFilterState<{
    jobs: string[];
    tags: Tag[];
    codeLocations: RepoAddress[];
  }>(FILTER_FIELDS);

  const state = useMemo(() => {
    return {
      ..._state,
      codeLocations: _state.codeLocations.map(({name, location}) =>
        buildRepoAddress(name, location),
      ),
    };
  }, [_state]);

  const codeLocationFilter = useCodeLocationFilter({
    codeLocations: state.codeLocations,
    setCodeLocations: setters.setCodeLocations,
  });

  const jobFilter = useStaticSetFilter<string>({
    name: 'Job',
    icon: 'job',
    allValues: useMemo(
      () =>
        allJobs.map((job) => ({
          key: job.name,
          value: job.name,
          match: [job.name],
        })),
      [allJobs],
    ),
    renderLabel: ({value}) => (
      <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
        <Icon name="job" />
        <TruncatedTextWithFullTextOnHover text={value} />
      </Box>
    ),
    getStringValue: (x) => x,
    state: state.jobs,
    onStateChanged: useCallback(
      (values) => {
        setters.setJobs(Array.from(values));
      },
      [setters],
    ),
  });

  const filters = useMemo(() => [codeLocationFilter, jobFilter], [codeLocationFilter, jobFilter]);
  const {button: filterButton, activeFiltersJsx} = useFilters({filters});

  const filteredRepoBuckets = useMemo(() => {
    return repoBuckets
      .filter((bucket) => {
        return !state.codeLocations.length || state.codeLocations.includes(bucket.repoAddress);
      })
      .map((bucket) => ({
        ...bucket,
        jobs: bucket.jobs.filter((job) => {
          if (state.jobs.length && !state.jobs.includes(job.name)) {
            return false;
          }
          return true;
        }),
      }))
      .filter((bucket) => !!bucket.jobs.length);
  }, [repoBuckets, state]);

  const content = () => {
    if (loading) {
      return (
        <Box flex={{direction: 'row', justifyContent: 'center'}} style={{paddingTop: '100px'}}>
          <Box flex={{direction: 'row', alignItems: 'center', gap: 16}}>
            <Spinner purpose="body-text" />
            <div style={{color: Colors.textLight()}}>Loading jobs…</div>
          </Box>
        </Box>
      );
    }

    if (!filteredRepoBuckets.length) {
      return (
        <Box padding={{top: 20}}>
          <NonIdealState
            icon="search"
            title="No jobs"
            description={
              repoBuckets.length
                ? 'No jobs were found that match your filters'
                : 'No jobs were found in your definitions'
            }
          />
        </Box>
      );
    }

    return <OverviewJobsTable repos={filteredRepoBuckets} />;
  };

  return (
    <>
      <Box
        padding={{horizontal: 24, vertical: 8}}
        flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between', grow: 0}}
        border="bottom"
      >
        {filterButton}
      </Box>
      {activeFiltersJsx.length ? (
        <Box
          padding={{vertical: 8, horizontal: 24}}
          border="bottom"
          flex={{direction: 'row', gap: 8}}
        >
          {activeFiltersJsx}
        </Box>
      ) : null}
      {loading && !repoCount ? (
        <Box padding={64}>
          <SpinnerWithText label="Loading jobs…" />
        </Box>
      ) : (
        content()
      )}
    </>
  );
};

type RepoBucket = {
  repoAddress: RepoAddress;
  jobs: WorkspacePipelineFragment[];
};

const buildBuckets = (
  locationEntries: Extract<WorkspaceLocationNodeFragment, {__typename: 'WorkspaceLocationEntry'}>[],
): RepoBucket[] => {
  const entries = locationEntries.map((entry) => entry.locationOrLoadError);
  const buckets = [];

  for (const entry of entries) {
    if (entry?.__typename !== 'RepositoryLocation') {
      continue;
    }

    for (const repo of entry.repositories) {
      const {name, pipelines} = repo;
      const repoAddress = buildRepoAddress(name, entry.name);
      const jobs = pipelines.filter(({name}) => !isHiddenAssetGroupJob(name));

      if (jobs.length > 0) {
        buckets.push({
          repoAddress,
          jobs,
        });
      }
    }
  }

  return sortRepoBuckets(buckets);
};
