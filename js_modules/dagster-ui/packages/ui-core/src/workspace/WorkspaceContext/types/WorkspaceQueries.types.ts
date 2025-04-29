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
                  tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                }>;
                sensors: Array<{
                  __typename: 'Sensor';
                  id: string;
                  name: string;
                  sensorType: Types.SensorType;
                  tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
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
                assetNodes: Array<{
                  __typename: 'AssetNode';
                  id: string;
                  changedReasons: Array<Types.ChangeReason>;
                  groupName: string;
                  opNames: Array<string>;
                  isMaterializable: boolean;
                  isObservable: boolean;
                  isExecutable: boolean;
                  isPartitioned: boolean;
                  isAutoCreatedStub: boolean;
                  computeKind: string | null;
                  hasMaterializePermission: boolean;
                  hasReportRunlessAssetEventPermission: boolean;
                  description: string | null;
                  pools: Array<string>;
                  jobNames: Array<string>;
                  kinds: Array<string>;
                  assetKey: {__typename: 'AssetKey'; path: Array<string>};
                  internalFreshnessPolicy: {
                    __typename: 'TimeWindowFreshnessPolicy';
                    failWindowSeconds: number;
                    warnWindowSeconds: number | null;
                  } | null;
                  partitionDefinition: {
                    __typename: 'PartitionDefinition';
                    description: string;
                    dimensionTypes: Array<{
                      __typename: 'DimensionDefinitionType';
                      type: Types.PartitionDefinitionType;
                      dynamicPartitionsDefinitionName: string | null;
                    }>;
                  } | null;
                  automationCondition: {
                    __typename: 'AutomationCondition';
                    label: string | null;
                    expandedLabel: Array<string>;
                  } | null;
                  owners: Array<
                    | {__typename: 'TeamAssetOwner'; team: string}
                    | {__typename: 'UserAssetOwner'; email: string}
                  >;
                  tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                  repository: {
                    __typename: 'Repository';
                    id: string;
                    name: string;
                    location: {__typename: 'RepositoryLocation'; id: string; name: string};
                  };
                }>;
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
            tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
          }>;
          sensors: Array<{
            __typename: 'Sensor';
            id: string;
            name: string;
            sensorType: Types.SensorType;
            tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
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
          assetNodes: Array<{
            __typename: 'AssetNode';
            id: string;
            changedReasons: Array<Types.ChangeReason>;
            groupName: string;
            opNames: Array<string>;
            isMaterializable: boolean;
            isObservable: boolean;
            isExecutable: boolean;
            isPartitioned: boolean;
            isAutoCreatedStub: boolean;
            computeKind: string | null;
            hasMaterializePermission: boolean;
            hasReportRunlessAssetEventPermission: boolean;
            description: string | null;
            pools: Array<string>;
            jobNames: Array<string>;
            kinds: Array<string>;
            assetKey: {__typename: 'AssetKey'; path: Array<string>};
            internalFreshnessPolicy: {
              __typename: 'TimeWindowFreshnessPolicy';
              failWindowSeconds: number;
              warnWindowSeconds: number | null;
            } | null;
            partitionDefinition: {
              __typename: 'PartitionDefinition';
              description: string;
              dimensionTypes: Array<{
                __typename: 'DimensionDefinitionType';
                type: Types.PartitionDefinitionType;
                dynamicPartitionsDefinitionName: string | null;
              }>;
            } | null;
            automationCondition: {
              __typename: 'AutomationCondition';
              label: string | null;
              expandedLabel: Array<string>;
            } | null;
            owners: Array<
              | {__typename: 'TeamAssetOwner'; team: string}
              | {__typename: 'UserAssetOwner'; email: string}
            >;
            tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
            repository: {
              __typename: 'Repository';
              id: string;
              name: string;
              location: {__typename: 'RepositoryLocation'; id: string; name: string};
            };
          }>;
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
      tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
    }>;
    sensors: Array<{
      __typename: 'Sensor';
      id: string;
      name: string;
      sensorType: Types.SensorType;
      tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
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
    assetNodes: Array<{
      __typename: 'AssetNode';
      id: string;
      changedReasons: Array<Types.ChangeReason>;
      groupName: string;
      opNames: Array<string>;
      isMaterializable: boolean;
      isObservable: boolean;
      isExecutable: boolean;
      isPartitioned: boolean;
      isAutoCreatedStub: boolean;
      computeKind: string | null;
      hasMaterializePermission: boolean;
      hasReportRunlessAssetEventPermission: boolean;
      description: string | null;
      pools: Array<string>;
      jobNames: Array<string>;
      kinds: Array<string>;
      assetKey: {__typename: 'AssetKey'; path: Array<string>};
      internalFreshnessPolicy: {
        __typename: 'TimeWindowFreshnessPolicy';
        failWindowSeconds: number;
        warnWindowSeconds: number | null;
      } | null;
      partitionDefinition: {
        __typename: 'PartitionDefinition';
        description: string;
        dimensionTypes: Array<{
          __typename: 'DimensionDefinitionType';
          type: Types.PartitionDefinitionType;
          dynamicPartitionsDefinitionName: string | null;
        }>;
      } | null;
      automationCondition: {
        __typename: 'AutomationCondition';
        label: string | null;
        expandedLabel: Array<string>;
      } | null;
      owners: Array<
        {__typename: 'TeamAssetOwner'; team: string} | {__typename: 'UserAssetOwner'; email: string}
      >;
      tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
      repository: {
        __typename: 'Repository';
        id: string;
        name: string;
        location: {__typename: 'RepositoryLocation'; id: string; name: string};
      };
    }>;
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
    tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
  }>;
  sensors: Array<{
    __typename: 'Sensor';
    id: string;
    name: string;
    sensorType: Types.SensorType;
    tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
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
  assetNodes: Array<{
    __typename: 'AssetNode';
    id: string;
    changedReasons: Array<Types.ChangeReason>;
    groupName: string;
    opNames: Array<string>;
    isMaterializable: boolean;
    isObservable: boolean;
    isExecutable: boolean;
    isPartitioned: boolean;
    isAutoCreatedStub: boolean;
    computeKind: string | null;
    hasMaterializePermission: boolean;
    hasReportRunlessAssetEventPermission: boolean;
    description: string | null;
    pools: Array<string>;
    jobNames: Array<string>;
    kinds: Array<string>;
    assetKey: {__typename: 'AssetKey'; path: Array<string>};
    internalFreshnessPolicy: {
      __typename: 'TimeWindowFreshnessPolicy';
      failWindowSeconds: number;
      warnWindowSeconds: number | null;
    } | null;
    partitionDefinition: {
      __typename: 'PartitionDefinition';
      description: string;
      dimensionTypes: Array<{
        __typename: 'DimensionDefinitionType';
        type: Types.PartitionDefinitionType;
        dynamicPartitionsDefinitionName: string | null;
      }>;
    } | null;
    automationCondition: {
      __typename: 'AutomationCondition';
      label: string | null;
      expandedLabel: Array<string>;
    } | null;
    owners: Array<
      {__typename: 'TeamAssetOwner'; team: string} | {__typename: 'UserAssetOwner'; email: string}
    >;
    tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
    repository: {
      __typename: 'Repository';
      id: string;
      name: string;
      location: {__typename: 'RepositoryLocation'; id: string; name: string};
    };
  }>;
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
  tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
};

export type WorkspaceSensorFragment = {
  __typename: 'Sensor';
  id: string;
  name: string;
  sensorType: Types.SensorType;
  tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
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

export const LocationWorkspaceQueryVersion = 'f92089484123ab96f4f87ccfc3ef84413e45a7c16b2cd6145e6f8c694283ac75';

export const CodeLocationStatusQueryVersion = 'f92885e073b8b4b9bd588bf248df7b06025e2a1f6e74c082233ac7863f5eef8e';
