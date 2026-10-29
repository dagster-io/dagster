/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type InstigationStatus = 'RUNNING' | 'STOPPED';

export type RunStatus =
  | 'CANCELED'
  | 'CANCELING'
  | 'FAILURE'
  | 'MANAGED'
  | 'NOT_STARTED'
  | 'QUEUED'
  | 'STARTED'
  | 'STARTING'
  | 'SUCCESS';

export type StepEventStatus = 'FAILURE' | 'IN_PROGRESS' | 'SKIPPED' | 'SUCCESS';

export type HillpointeRunMetricsQueryVariables = Exact<{
  after: number;
  limit: number;
}>;

export type HillpointeRunMetricsQuery = {
  __typename: 'Query';
  runsOrError:
    | {__typename: 'InvalidPipelineRunsFilterError'}
    | {__typename: 'PythonError'}
    | {
        __typename: 'Runs';
        results: Array<{
          __typename: 'Run';
          id: string;
          runId: string;
          jobName: string;
          status: Types.RunStatus;
          creationTime: number;
          startTime: number | null;
          endTime: number | null;
        }>;
      };
};

export type HillpointeRunStatsQueryVariables = Exact<{
  after: number;
  limit: number;
}>;

export type HillpointeRunStatsQuery = {
  __typename: 'Query';
  runsOrError:
    | {__typename: 'InvalidPipelineRunsFilterError'}
    | {__typename: 'PythonError'}
    | {
        __typename: 'Runs';
        results: Array<{
          __typename: 'Run';
          id: string;
          runId: string;
          stats:
            | {__typename: 'PythonError'}
            | {
                __typename: 'RunStatsSnapshot';
                id: string;
                stepsSucceeded: number;
                stepsFailed: number;
                materializations: number;
              };
        }>;
      };
};

export type HillpointeRunHistoryQueryVariables = Exact<{
  after: number;
}>;

export type HillpointeRunHistoryQuery = {
  __typename: 'Query';
  runsOrError:
    | {__typename: 'InvalidPipelineRunsFilterError'}
    | {__typename: 'PythonError'}
    | {
        __typename: 'Runs';
        results: Array<{
          __typename: 'Run';
          id: string;
          status: Types.RunStatus;
          creationTime: number;
        }>;
      };
};

export type HillpointeRowCountQueryVariables = Exact<{
  after: number;
}>;

export type HillpointeRowCountQuery = {
  __typename: 'Query';
  runsOrError:
    | {__typename: 'InvalidPipelineRunsFilterError'}
    | {__typename: 'PythonError'}
    | {
        __typename: 'Runs';
        results: Array<{
          __typename: 'Run';
          id: string;
          startTime: number | null;
          assetMaterializations: Array<{
            __typename: 'MaterializationEvent';
            metadataEntries: Array<
              | {__typename: 'AssetMetadataEntry'; label: string}
              | {__typename: 'BoolMetadataEntry'; label: string}
              | {__typename: 'CodeReferencesMetadataEntry'; label: string}
              | {__typename: 'FloatMetadataEntry'; label: string}
              | {__typename: 'IntMetadataEntry'; intRepr: string; label: string}
              | {__typename: 'JobMetadataEntry'; label: string}
              | {__typename: 'JsonMetadataEntry'; label: string}
              | {__typename: 'MarkdownMetadataEntry'; label: string}
              | {__typename: 'NotebookMetadataEntry'; label: string}
              | {__typename: 'NullMetadataEntry'; label: string}
              | {__typename: 'PathMetadataEntry'; label: string}
              | {__typename: 'PipelineRunMetadataEntry'; label: string}
              | {__typename: 'PoolMetadataEntry'; label: string}
              | {__typename: 'PythonArtifactMetadataEntry'; label: string}
              | {__typename: 'TableColumnLineageMetadataEntry'; label: string}
              | {__typename: 'TableMetadataEntry'; label: string}
              | {__typename: 'TableSchemaMetadataEntry'; label: string}
              | {__typename: 'TextMetadataEntry'; label: string}
              | {__typename: 'TimestampMetadataEntry'; label: string}
              | {__typename: 'UrlMetadataEntry'; label: string}
            >;
          }>;
        }>;
      };
};

export type HillpointeSchedulesQueryVariables = Exact<{[key: string]: never}>;

export type HillpointeSchedulesQuery = {
  __typename: 'Query';
  workspaceOrError:
    | {__typename: 'PythonError'}
    | {
        __typename: 'Workspace';
        id: string;
        locationEntries: Array<{
          __typename: 'WorkspaceLocationEntry';
          id: string;
          locationOrLoadError:
            | {__typename: 'PythonError'}
            | {
                __typename: 'RepositoryLocation';
                id: string;
                repositories: Array<{
                  __typename: 'Repository';
                  id: string;
                  schedules: Array<{
                    __typename: 'Schedule';
                    id: string;
                    pipelineName: string;
                    scheduleState: {
                      __typename: 'InstigationState';
                      id: string;
                      status: Types.InstigationStatus;
                    };
                    futureTicks: {
                      __typename: 'DryRunInstigationTicks';
                      results: Array<{
                        __typename: 'DryRunInstigationTick';
                        timestamp: number | null;
                      }>;
                    };
                  }>;
                }>;
              }
            | null;
        }>;
      };
};

export type HillpointeRunStepStatsQueryVariables = Exact<{
  runId: string;
}>;

export type HillpointeRunStepStatsQuery = {
  __typename: 'Query';
  runOrError:
    | {__typename: 'PythonError'}
    | {
        __typename: 'Run';
        id: string;
        stepStats: Array<{
          __typename: 'RunStepStats';
          stepKey: string;
          status: Types.StepEventStatus | null;
          startTime: number | null;
          endTime: number | null;
          attempts: Array<{__typename: 'RunMarker'; startTime: number | null}>;
        }>;
      }
    | {__typename: 'RunNotFoundError'};
};
