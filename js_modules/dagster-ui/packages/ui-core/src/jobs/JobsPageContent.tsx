import {Box, Colors, NonIdealState, Spinner, SpinnerWithText} from '@dagster-io/ui-components';
import {useContext, useMemo} from 'react';

import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {filterJobSelectionByQuery} from '../job-selection/AntlrJobSelection';
import {JobSelectionInput} from '../job-selection/input/JobSelectionInput';
import {OverviewJobsTable} from '../overview/OverviewJobsTable';
import {sortRepoBuckets} from '../overview/sortRepoBuckets';
import {visibleRepoKeys} from '../overview/visibleRepoKeys';
import {WorkspaceContext} from '../workspace/WorkspaceContext/WorkspaceContext';
import {WorkspaceLocationNodeFragment} from '../workspace/WorkspaceContext/types/WorkspaceQueries.types';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';

export const JobsPageContent = () => {
  const {
    allRepos,
    visibleRepos,
    loadingNonAssets: loading,
    data: cachedData,
  } = useContext(WorkspaceContext);
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

  const [selection, setSelection] = useQueryPersistedState<string>({
    queryKey: 'selection',
    defaults: {selection: ''},
    behavior: 'push',
  });

  const allJobs = useMemo(() => {
    return repoBuckets.flatMap((bucket) => bucket.jobs);
  }, [repoBuckets]);

  const filteredJobs = useMemo(() => {
    return filterJobSelectionByQuery(allJobs, selection).all;
  }, [allJobs, selection]);

  const filteredRepoBuckets = useMemo(() => {
    return repoBuckets
      .filter((bucket) => {
        return Array.from(filteredJobs).some(
          (job) =>
            job.repo.name === bucket.repoAddress.name &&
            job.repo.location === bucket.repoAddress.location,
        );
      })
      .map((bucket) => ({
        ...bucket,
        jobs: bucket.jobs.filter((job) => {
          return filteredJobs.has(job);
        }),
      }))
      .filter((bucket) => !!bucket.jobs.length);
  }, [repoBuckets, filteredJobs]);

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
      <Box padding={{horizontal: 24, vertical: 12}} border="bottom">
        <JobSelectionInput items={allJobs} value={selection} onChange={setSelection} />
      </Box>
      {loading && !repoCount ? (
        <Box padding={64} flex={{direction: 'row', justifyContent: 'center'}}>
          <SpinnerWithText label="Loading jobs…" />
        </Box>
      ) : (
        content()
      )}
    </>
  );
};

const buildBuckets = (
  locationEntries: Extract<WorkspaceLocationNodeFragment, {__typename: 'WorkspaceLocationEntry'}>[],
) => {
  const entries = locationEntries.map((entry) => entry.locationOrLoadError);
  const buckets = [];

  for (const entry of entries) {
    if (entry?.__typename !== 'RepositoryLocation') {
      continue;
    }

    for (const repo of entry.repositories) {
      const {name, pipelines} = repo;
      const repoAddress = buildRepoAddress(name, entry.name);
      const jobs = pipelines
        .filter(({name}) => !isHiddenAssetGroupJob(name))
        .map((job) => ({
          ...job,
          repo: {
            name: repoAddress.name,
            location: repoAddress.location,
          },
        }));

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
