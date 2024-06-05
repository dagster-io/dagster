// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type LocationWorkspaceQueryVariables = Types.Exact<{
  name: Types.Scalars['String']['input'];
}>;

export type LocationWorkspaceQuery = {
  __typename: 'Query';
  workspaceLocationEntryOrError:
    | {__typename: 'PythonError'}
    | {
        __typename: 'WorkspaceLocationEntry';
        id: string;
        name: string;
        loadStatus: Types.RepositoryLocationLoadStatus;
        updatedTimestamp: number;
        displayMetadata: Array<{__typename: 'RepositoryMetadata'; key: string; value: string}>;
        featureFlags: Array<{__typename: 'FeatureFlag'; name: string; enabled: boolean}>;
        locationOrLoadError:
          | {
              __typename: 'PythonError';
              message: string;
              stack: Array<string>;
              errorChain: Array<{
                __typename: 'ErrorChainLink';
                isExplicitLink: boolean;
                error: {__typename: 'PythonError'; message: string; stack: Array<string>};
              }>;
            }
          | {
              __typename: 'RepositoryLocation';
              id: string;
              name: string;
              dagsterLibraryVersions: Array<{
                __typename: 'DagsterLibraryVersion';
                name: string;
                version: string;
              }> | null;
              repositories: Array<{
                __typename: 'Repository';
                id: string;
                name: string;
                pipelines: Array<{
                  __typename: 'Pipeline';
                  id: string;
                  name: string;
                  isJob: boolean;
                  isAssetJob: boolean;
                  pipelineSnapshotId: string;
                }>;
                schedules: Array<{
                  __typename: 'Schedule';
                  id: string;
                  name: string;
                  cronSchedule: string;
                  executionTimezone: string | null;
                  mode: string;
                  pipelineName: string;
                  scheduleState: {
                    __typename: 'InstigationState';
                    id: string;
                    selectorId: string;
                    status: Types.InstigationStatus;
                  };
                }>;
                sensors: Array<{
                  __typename: 'Sensor';
                  id: string;
                  name: string;
                  jobOriginId: string;
                  sensorType: Types.SensorType;
                  targets: Array<{__typename: 'Target'; mode: string; pipelineName: string}> | null;
                  sensorState: {
                    __typename: 'InstigationState';
                    id: string;
                    selectorId: string;
                    status: Types.InstigationStatus;
                  };
                }>;
                partitionSets: Array<{
                  __typename: 'PartitionSet';
                  id: string;
                  mode: string;
                  pipelineName: string;
                }>;
                assetGroups: Array<{__typename: 'AssetGroup'; id: string; groupName: string}>;
                allTopLevelResourceDetails: Array<{
                  __typename: 'ResourceDetails';
                  id: string;
                  name: string;
                }>;
              }>;
            }
          | null;
      }
    | null;
};

export type CodeLocationStatusQueryVariables = Types.Exact<{[key: string]: never}>;

export type CodeLocationStatusQuery = {
  __typename: 'Query';
  locationStatusesOrError:
    | {__typename: 'PythonError'}
    | {
        __typename: 'WorkspaceLocationStatusEntries';
        entries: Array<{
          __typename: 'WorkspaceLocationStatusEntry';
          id: string;
          name: string;
          loadStatus: Types.RepositoryLocationLoadStatus;
          updateTimestamp: number;
        }>;
      };
};
