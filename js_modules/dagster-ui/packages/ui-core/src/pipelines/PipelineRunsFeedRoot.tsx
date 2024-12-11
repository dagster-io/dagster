import {
  Box,
  ButtonLink,
  Checkbox,
  Tag,
  TokenizingFieldValue,
  tokenToString,
} from '@dagster-io/ui-components';
import {useCallback, useMemo} from 'react';
import {useParams} from 'react-router-dom';

import {explorerPathFromString} from './PipelinePathUtils';
import {PipelineRunsEmptyState} from './PipelineRunsEmptyState';
import {useJobTitle} from './useJobTitle';
import {
  FIFTEEN_SECONDS,
  QueryRefreshCountdown,
  useQueryRefreshAtInterval,
} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {RunsFeedView, RunsFilter} from '../graphql/types';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {DagsterTag} from '../runs/RunTag';
import {RunsQueryRefetchContext} from '../runs/RunUtils';
import {RunsFeedError} from '../runs/RunsFeedError';
import {RunsFeedTable} from '../runs/RunsFeedTable';
import {
  RunFilterToken,
  RunFilterTokenType,
  runsFilterForSearchTokens,
  useQueryPersistedRunFilters,
  useRunsFilterInput,
} from '../runs/RunsFilterInput';
import {useRunsFeedEntries} from '../runs/useRunsFeedEntries';
import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext/util';
import {repoAddressAsTag} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

const ENABLED_FILTERS: RunFilterTokenType[] = [
  'status',
  'tag',
  'id',
  'created_date_before',
  'created_date_after',
];

export const PipelineRunsFeedRoot = (props: {repoAddress?: RepoAddress}) => {
  useTrackPageView();

  const {pipelinePath} = useParams<{pipelinePath: string}>();
  const {repoAddress = null} = props;
  const explorerPath = explorerPathFromString(pipelinePath);
  const {pipelineName, snapshotId} = explorerPath;

  const repo = useRepository(repoAddress);
  const isJob = isThisThingAJob(repo, pipelineName);

  useJobTitle(explorerPath, isJob);

  const [filterTokens, setFilterTokens] = useQueryPersistedRunFilters(ENABLED_FILTERS);

  const permanentTokens = useMemo(() => {
    return [
      isJob ? {token: 'job', value: pipelineName} : {token: 'pipeline', value: pipelineName},
      snapshotId ? {token: 'snapshotId', value: snapshotId} : null,
    ].filter(Boolean) as TokenizingFieldValue[];
  }, [isJob, pipelineName, snapshotId]);

  const [view, setView] = useQueryPersistedState<RunsFeedView>({
    queryKey: 'view',
    defaults: {view: RunsFeedView.ROOTS},
  });

  const runsFilter: RunsFilter = useMemo(() => {
    const allTokens = [...filterTokens, ...permanentTokens];
    if (repoAddress) {
      const repoToken = {
        token: 'tag',
        value: `${DagsterTag.RepositoryLabelTag}=${repoAddressAsTag(repoAddress)}`,
      };
      allTokens.push(repoToken);
    }
    return {...runsFilterForSearchTokens(allTokens), pipelineName, snapshotId};
  }, [filterTokens, permanentTokens, pipelineName, repoAddress, snapshotId]);

  const onAddTag = useCallback(
    (token: RunFilterToken) => {
      const tokenAsString = tokenToString(token);
      if (!filterTokens.some((token) => tokenToString(token) === tokenAsString)) {
        setFilterTokens([...filterTokens, token]);
      }
    },
    [filterTokens, setFilterTokens],
  );

  const {entries, paginationProps, queryResult} = useRunsFeedEntries(runsFilter, 'all', view);

  const refreshState = useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);

  const {button, activeFiltersJsx} = useRunsFilterInput({
    enabledFilters: ENABLED_FILTERS,
    tokens: filterTokens,
    onChange: setFilterTokens,
    loading: queryResult.loading,
  });

  const actionBarComponents = (
    <Box
      flex={{direction: 'row', gap: 8, alignItems: 'center'}}
      style={{width: '100%'}}
      padding={{right: 16}}
    >
      {button}
      <Checkbox
        label={<span>Show runs within backfills</span>}
        checked={view === RunsFeedView.RUNS}
        onChange={() => {
          setView(view === RunsFeedView.RUNS ? RunsFeedView.ROOTS : RunsFeedView.RUNS);
        }}
      />
      <div style={{flex: 1}} />
      <QueryRefreshCountdown refreshState={refreshState} />
    </Box>
  );

  const belowActionBarComponents = (
    <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
      {permanentTokens.map(({token, value}) => (
        <Tag key={token}>{`${token}:${value}`}</Tag>
      ))}
      {activeFiltersJsx}
      {activeFiltersJsx.length > 0 && (
        <ButtonLink onClick={() => setFilterTokens([])}>Clear all</ButtonLink>
      )}
    </Box>
  );

  function content() {
    if (queryResult.error) {
      return <RunsFeedError error={queryResult.error} />;
    }

    return (
      <div style={{minHeight: 0}}>
        <RunsFeedTable
          entries={entries}
          loading={queryResult.loading}
          onAddTag={onAddTag}
          refetch={refreshState.refetch}
          actionBarComponents={actionBarComponents}
          belowActionBarComponents={belowActionBarComponents}
          paginationProps={paginationProps}
          filter={runsFilter}
          emptyState={() => (
            <PipelineRunsEmptyState
              repoAddress={repoAddress}
              anyFilter={filterTokens.length > 0}
              jobName={pipelineName}
              jobPath={pipelinePath}
            />
          )}
        />
      </div>
    );
  }

  return (
    <RunsQueryRefetchContext.Provider value={{refetch: refreshState.refetch}}>
      {content()}
    </RunsQueryRefetchContext.Provider>
  );
};
