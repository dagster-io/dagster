import {
  Box,
  ButtonLink,
  CursorHistoryControls,
  Icon,
  NonIdealState,
  Page,
  Tag,
  TokenizingFieldValue,
  tokenToString,
} from '@dagster-io/ui-components';
import {useCallback, useMemo} from 'react';
import {useParams} from 'react-router-dom';

import {explorerPathFromString} from './PipelinePathUtils';
import {
  PipelineRunsRootQuery,
  PipelineRunsRootQueryVariables,
} from './types/PipelineRunsRoot.types';
import {useJobTitle} from './useJobTitle';
import {gql} from '../apollo-client';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {
  FIFTEEN_SECONDS,
  QueryRefreshCountdown,
  useQueryRefreshAtInterval,
} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {RunTable} from '../runs/RunTable';
import {RUN_TABLE_RUN_FRAGMENT} from '../runs/RunTableRunFragment';
import {DagsterTag} from '../runs/RunTag';
import {RunsQueryRefetchContext} from '../runs/RunUtils';
import {
  RunFilterToken,
  RunFilterTokenType,
  runsFilterForSearchTokens,
  useQueryPersistedRunFilters,
  useRunsFilterInput,
} from '../runs/RunsFilterInput';
import {useCursorPaginatedQuery} from '../runs/useCursorPaginatedQuery';
import {AnchorButton} from '../ui/AnchorButton';
import {Loading} from '../ui/Loading';
import {StickyTableContainer} from '../ui/StickyTableContainer';
import {
  isThisThingAJob,
  isThisThingAnAssetJob,
  useRepository,
} from '../workspace/WorkspaceContext/util';
import {repoAddressAsTag} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

const PAGE_SIZE = 25;
const ENABLED_FILTERS: RunFilterTokenType[] = [
  'status',
  'tag',
  'id',
  'created_date_before',
  'created_date_after',
];

interface Props {
  repoAddress?: RepoAddress;
}

export const PipelineRunsRoot = (props: Props) => {
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

  const allTokens = [...filterTokens, ...permanentTokens];
  if (repoAddress) {
    const repoToken = {
      token: 'tag',
      value: `${DagsterTag.RepositoryLabelTag}=${repoAddressAsTag(repoAddress)}`,
    };
    allTokens.push(repoToken);
  }

  const {queryResult, paginationProps} = useCursorPaginatedQuery<
    PipelineRunsRootQuery,
    PipelineRunsRootQueryVariables
  >({
    query: PIPELINE_RUNS_ROOT_QUERY,
    pageSize: PAGE_SIZE,
    variables: {
      filter: {...runsFilterForSearchTokens(allTokens), pipelineName, snapshotId},
    },
    nextCursorForResult: (runs) => {
      if (runs.pipelineRunsOrError.__typename !== 'Runs') {
        return undefined;
      }
      return runs.pipelineRunsOrError.results[PAGE_SIZE - 1]?.id;
    },
    getResultArray: (data) => {
      if (!data || data.pipelineRunsOrError.__typename !== 'Runs') {
        return [];
      }
      return data.pipelineRunsOrError.results;
    },
  });

  const onAddTag = useCallback(
    (token: RunFilterToken) => {
      const tokenAsString = tokenToString(token);
      if (!filterTokens.some((token) => tokenToString(token) === tokenAsString)) {
        setFilterTokens([...filterTokens, token]);
      }
    },
    [filterTokens, setFilterTokens],
  );

  const refreshState = useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);
  const {button, activeFiltersJsx} = useRunsFilterInput({
    enabledFilters: ENABLED_FILTERS,
    tokens: filterTokens,
    onChange: setFilterTokens,
    loading: queryResult.loading,
  });

  return (
    <RunsQueryRefetchContext.Provider value={{refetch: queryResult.refetch}}>
      <Page>
        <Loading queryResult={queryResult} allowStaleData={true}>
          {({pipelineRunsOrError}) => {
            if (pipelineRunsOrError.__typename !== 'Runs') {
              return (
                <Box padding={{vertical: 64}}>
                  <NonIdealState
                    icon="error"
                    title="Query Error"
                    description={pipelineRunsOrError.message}
                  />
                </Box>
              );
            }

            const runs = pipelineRunsOrError.results;

            const displayed = runs.slice(0, PAGE_SIZE);
            const {hasNextCursor, hasPrevCursor} = paginationProps;

            return (
              <>
                <StickyTableContainer $top={0}>
                  <RunTable
                    runs={displayed}
                    onAddTag={onAddTag}
                    actionBarComponents={
                      <Box
                        flex={{
                          direction: 'row',
                          justifyContent: 'space-between',
                          grow: 1,
                          alignItems: 'center',
                          gap: 4,
                        }}
                        margin={{right: 8}}
                      >
                        {button}
                        <QueryRefreshCountdown refreshState={refreshState} />
                      </Box>
                    }
                    belowActionBarComponents={
                      <>
                        {permanentTokens.map(({token, value}) => (
                          <Tag key={token}>{`${token}:${value}`}</Tag>
                        ))}
                        {activeFiltersJsx.length ? (
                          <>
                            {activeFiltersJsx}
                            <ButtonLink
                              onClick={() => {
                                setFilterTokens([]);
                              }}
                            >
                              Clear all
                            </ButtonLink>
                          </>
                        ) : null}
                      </>
                    }
                    emptyState={() => (
                      <EmptyState
                        repoAddress={repoAddress}
                        anyFilter={filterTokens.length > 0}
                        jobName={pipelineName}
                        jobPath={pipelinePath}
                      />
                    )}
                  />
                </StickyTableContainer>
                {hasNextCursor || hasPrevCursor ? (
                  <div style={{marginTop: '20px'}}>
                    <CursorHistoryControls {...paginationProps} />
                  </div>
                ) : null}
              </>
            );
          }}
        </Loading>
      </Page>
    </RunsQueryRefetchContext.Provider>
  );
};

interface EmptyStateProps {
  repoAddress: RepoAddress | null;
  jobName: string;
  jobPath: string;
  anyFilter: boolean;
}

const EmptyState = (props: EmptyStateProps) => {
  const {repoAddress, anyFilter, jobName, jobPath} = props;

  const repo = useRepository(repoAddress);
  const isAssetJob = isThisThingAnAssetJob(repo, jobName);

  const description = () => {
    if (!repoAddress) {
      return <div>You have not launched any runs for this job.</div>;
    }

    if (isAssetJob) {
      return (
        <Box flex={{direction: 'column', gap: 12}}>
          <div>
            {anyFilter
              ? 'There are no matching runs for these filters.'
              : 'You have not materialized any assets with this job yet.'}
          </div>
          <div>
            <AnchorButton
              icon={<Icon name="materialization" />}
              to={workspacePathFromAddress(repoAddress, `/jobs/${jobPath}`)}
            >
              Materialize an asset
            </AnchorButton>
          </div>
        </Box>
      );
    }

    return (
      <Box flex={{direction: 'column', gap: 12}}>
        <div>
          {anyFilter
            ? 'There are no matching runs for these filters.'
            : 'You have not launched any runs for this job yet.'}
        </div>
        <div>
          <AnchorButton
            icon={<Icon name="add_circle" />}
            to={workspacePathFromAddress(repoAddress, `/jobs/${jobPath}/playground`)}
          >
            Launch a run
          </AnchorButton>
        </div>
      </Box>
    );
  };

  return (
    <Box padding={{vertical: 64}}>
      <NonIdealState icon="run" title="No runs found" description={description()} />
    </Box>
  );
};

const PIPELINE_RUNS_ROOT_QUERY = gql`
  query PipelineRunsRootQuery($limit: Int, $cursor: String, $filter: RunsFilter!) {
    pipelineRunsOrError(limit: $limit, cursor: $cursor, filter: $filter) {
      ... on Runs {
        results {
          id
          ...RunTableRunFragment
        }
      }
      ... on InvalidPipelineRunsFilterError {
        message
      }
      ...PythonErrorFragment
    }
  }

  ${RUN_TABLE_RUN_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;
