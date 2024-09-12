// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type LocationWorkspaceQueryVariables = Types.Exact<{
  name: Types.Scalars['String']['input'];
}>;

export type LocationWorkspaceQuery = {
  __typename: 'Query';
  workspaceLocationEntryOrError:
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
        __typename: 'WorkspaceLocationEntry';
        id: string;
        name: string;
        loadStatus: Types.RepositoryLocationLoadStatus;
        updatedTimestamp: number;
        versionKey: string;
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
                    status: Types.InstigationStatus;
                    selectorId: string;
                    hasStartPermission: boolean;
                    hasStopPermission: boolean;
                  };
                }>;
                sensors: Array<{
                  __typename: 'Sensor';
                  id: string;
                  name: string;
                  sensorType: Types.SensorType;
                  targets: Array<{__typename: 'Target'; mode: string; pipelineName: string}> | null;
                  sensorState: {
                    __typename: 'InstigationState';
                    id: string;
                    status: Types.InstigationStatus;
                    selectorId: string;
                    hasStartPermission: boolean;
                    hasStopPermission: boolean;
                    typeSpecificData:
                      | {__typename: 'ScheduleData'}
                      | {__typename: 'SensorData'; lastCursor: string | null}
                      | null;
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
                  description: string | null;
                  resourceType: string;
                  schedulesUsing: Array<string>;
                  sensorsUsing: Array<string>;
                  parentResources: Array<{__typename: 'NestedResourceEntry'; name: string}>;
                  assetKeysUsing: Array<{__typename: 'AssetKey'; path: Array<string>}>;
                  jobsOpsUsing: Array<{__typename: 'JobWithOps'; jobName: string}>;
                }>;
                location: {__typename: 'RepositoryLocation'; id: string; name: string};
                displayMetadata: Array<{
                  __typename: 'RepositoryMetadata';
                  key: string;
                  value: string;
                }>;
              }>;
            }
          | null;
      }
    | null;
};

export type WorkspaceLocationNodeFragment = {
  __typename: 'WorkspaceLocationEntry';
  id: string;
  name: string;
  loadStatus: Types.RepositoryLocationLoadStatus;
  updatedTimestamp: number;
  versionKey: string;
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
              status: Types.InstigationStatus;
              selectorId: string;
              hasStartPermission: boolean;
              hasStopPermission: boolean;
            };
          }>;
          sensors: Array<{
            __typename: 'Sensor';
            id: string;
            name: string;
            sensorType: Types.SensorType;
            targets: Array<{__typename: 'Target'; mode: string; pipelineName: string}> | null;
            sensorState: {
              __typename: 'InstigationState';
              id: string;
              status: Types.InstigationStatus;
              selectorId: string;
              hasStartPermission: boolean;
              hasStopPermission: boolean;
              typeSpecificData:
                | {__typename: 'ScheduleData'}
                | {__typename: 'SensorData'; lastCursor: string | null}
                | null;
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
            description: string | null;
            resourceType: string;
            schedulesUsing: Array<string>;
            sensorsUsing: Array<string>;
            parentResources: Array<{__typename: 'NestedResourceEntry'; name: string}>;
            assetKeysUsing: Array<{__typename: 'AssetKey'; path: Array<string>}>;
            jobsOpsUsing: Array<{__typename: 'JobWithOps'; jobName: string}>;
          }>;
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
        status: Types.InstigationStatus;
        selectorId: string;
        hasStartPermission: boolean;
        hasStopPermission: boolean;
      };
    }>;
    sensors: Array<{
      __typename: 'Sensor';
      id: string;
      name: string;
      sensorType: Types.SensorType;
      targets: Array<{__typename: 'Target'; mode: string; pipelineName: string}> | null;
      sensorState: {
        __typename: 'InstigationState';
        id: string;
        status: Types.InstigationStatus;
        selectorId: string;
        hasStartPermission: boolean;
        hasStopPermission: boolean;
        typeSpecificData:
          | {__typename: 'ScheduleData'}
          | {__typename: 'SensorData'; lastCursor: string | null}
          | null;
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
      description: string | null;
      resourceType: string;
      schedulesUsing: Array<string>;
      sensorsUsing: Array<string>;
      parentResources: Array<{__typename: 'NestedResourceEntry'; name: string}>;
      assetKeysUsing: Array<{__typename: 'AssetKey'; path: Array<string>}>;
      jobsOpsUsing: Array<{__typename: 'JobWithOps'; jobName: string}>;
    }>;
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
      status: Types.InstigationStatus;
      selectorId: string;
      hasStartPermission: boolean;
      hasStopPermission: boolean;
    };
  }>;
  sensors: Array<{
    __typename: 'Sensor';
    id: string;
    name: string;
    sensorType: Types.SensorType;
    targets: Array<{__typename: 'Target'; mode: string; pipelineName: string}> | null;
    sensorState: {
      __typename: 'InstigationState';
      id: string;
      status: Types.InstigationStatus;
      selectorId: string;
      hasStartPermission: boolean;
      hasStopPermission: boolean;
      typeSpecificData:
        | {__typename: 'ScheduleData'}
        | {__typename: 'SensorData'; lastCursor: string | null}
        | null;
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
    description: string | null;
    resourceType: string;
    schedulesUsing: Array<string>;
    sensorsUsing: Array<string>;
    parentResources: Array<{__typename: 'NestedResourceEntry'; name: string}>;
    assetKeysUsing: Array<{__typename: 'AssetKey'; path: Array<string>}>;
    jobsOpsUsing: Array<{__typename: 'JobWithOps'; jobName: string}>;
  }>;
  location: {__typename: 'RepositoryLocation'; id: string; name: string};
  displayMetadata: Array<{__typename: 'RepositoryMetadata'; key: string; value: string}>;
};

export type WorkspacePipelineFragment = {
  __typename: 'Pipeline';
  id: string;
  name: string;
  isJob: boolean;
  isAssetJob: boolean;
  pipelineSnapshotId: string;
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
    status: Types.InstigationStatus;
    selectorId: string;
    hasStartPermission: boolean;
    hasStopPermission: boolean;
  };
};

export type WorkspaceSensorFragment = {
  __typename: 'Sensor';
  id: string;
  name: string;
  sensorType: Types.SensorType;
  targets: Array<{__typename: 'Target'; mode: string; pipelineName: string}> | null;
  sensorState: {
    __typename: 'InstigationState';
    id: string;
    status: Types.InstigationStatus;
    selectorId: string;
    hasStartPermission: boolean;
    hasStopPermission: boolean;
    typeSpecificData:
      | {__typename: 'ScheduleData'}
      | {__typename: 'SensorData'; lastCursor: string | null}
      | null;
  };
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
          versionKey: string;
        }>;
      };
};

export type LocationStatusEntryFragment = {
  __typename: 'WorkspaceLocationStatusEntry';
  id: string;
  name: string;
  loadStatus: Types.RepositoryLocationLoadStatus;
  updateTimestamp: number;
  versionKey: string;
};

export const LocationWorkspaceQueryVersion = '611c0706fbdde2c2159648e1a0d70a2ab23f79b7ef4e8bfc9a3ee4e50ff6dad2';

export const CodeLocationStatusQueryVersion = 'f92885e073b8b4b9bd588bf248df7b06025e2a1f6e74c082233ac7863f5eef8e';
