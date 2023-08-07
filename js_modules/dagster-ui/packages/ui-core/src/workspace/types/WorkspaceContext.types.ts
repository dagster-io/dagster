// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RootWorkspaceQueryVariables = Types.Exact<{[key: string]: never}>;

export type RootWorkspaceQuery = {
  __typename: 'Query';
  workspaceOrError:
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
        __typename: 'Workspace';
        id: string;
        locationEntries: Array<{
          __typename: 'WorkspaceLocationEntry';
          id: string;
          name: string;
          loadStatus: Types.RepositoryLocationLoadStatus;
          updatedTimestamp: number;
          displayMetadata: Array<{__typename: 'RepositoryMetadata'; key: string; value: string}>;
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
                isReloadSupported: boolean;
                serverId: string | null;
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
                    cronSchedule: string;
                    executionTimezone: string | null;
                    mode: string;
                    name: string;
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
                    jobOriginId: string;
                    name: string;
                    targets: Array<{
                      __typename: 'Target';
                      mode: string;
                      pipelineName: string;
                    }> | null;
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
                  assetGroups: Array<{__typename: 'AssetGroup'; groupName: string}>;
                  allTopLevelResourceDetails: Array<{__typename: 'ResourceDetails'; name: string}>;
                  location: {__typename: 'RepositoryLocation'; id: string; name: string};
                  displayMetadata: Array<{
                    __typename: 'RepositoryMetadata';
                    key: string;
                    value: string;
                  }>;
                }>;
              }
            | null;
        }>;
      };
};

export type WorkspaceLocationNodeFragment = {
  __typename: 'WorkspaceLocationEntry';
  id: string;
  name: string;
  loadStatus: Types.RepositoryLocationLoadStatus;
  updatedTimestamp: number;
  displayMetadata: Array<{__typename: 'RepositoryMetadata'; key: string; value: string}>;
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
        isReloadSupported: boolean;
        serverId: string | null;
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
            cronSchedule: string;
            executionTimezone: string | null;
            mode: string;
            name: string;
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
            jobOriginId: string;
            name: string;
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
          assetGroups: Array<{__typename: 'AssetGroup'; groupName: string}>;
          allTopLevelResourceDetails: Array<{__typename: 'ResourceDetails'; name: string}>;
          location: {__typename: 'RepositoryLocation'; id: string; name: string};
          displayMetadata: Array<{__typename: 'RepositoryMetadata'; key: string; value: string}>;
        }>;
      }
    | null;
};

export type WorkspaceDisplayMetadataFragment = {
  __typename: 'RepositoryMetadata';
  key: string;
  value: string;
};

export type WorkspaceLocationFragment = {
  __typename: 'RepositoryLocation';
  id: string;
  isReloadSupported: boolean;
  serverId: string | null;
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
      cronSchedule: string;
      executionTimezone: string | null;
      mode: string;
      name: string;
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
      jobOriginId: string;
      name: string;
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
    assetGroups: Array<{__typename: 'AssetGroup'; groupName: string}>;
    allTopLevelResourceDetails: Array<{__typename: 'ResourceDetails'; name: string}>;
    location: {__typename: 'RepositoryLocation'; id: string; name: string};
    displayMetadata: Array<{__typename: 'RepositoryMetadata'; key: string; value: string}>;
  }>;
};

export type WorkspaceRepositoryFragment = {
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
    cronSchedule: string;
    executionTimezone: string | null;
    mode: string;
    name: string;
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
    jobOriginId: string;
    name: string;
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
  assetGroups: Array<{__typename: 'AssetGroup'; groupName: string}>;
  allTopLevelResourceDetails: Array<{__typename: 'ResourceDetails'; name: string}>;
  location: {__typename: 'RepositoryLocation'; id: string; name: string};
  displayMetadata: Array<{__typename: 'RepositoryMetadata'; key: string; value: string}>;
};

export type WorkspaceScheduleFragment = {
  __typename: 'Schedule';
  id: string;
  cronSchedule: string;
  executionTimezone: string | null;
  mode: string;
  name: string;
  pipelineName: string;
  scheduleState: {
    __typename: 'InstigationState';
    id: string;
    selectorId: string;
    status: Types.InstigationStatus;
  };
};

export type WorkspaceSensorFragment = {
  __typename: 'Sensor';
  id: string;
  jobOriginId: string;
  name: string;
  targets: Array<{__typename: 'Target'; mode: string; pipelineName: string}> | null;
  sensorState: {
    __typename: 'InstigationState';
    id: string;
    selectorId: string;
    status: Types.InstigationStatus;
  };
};
