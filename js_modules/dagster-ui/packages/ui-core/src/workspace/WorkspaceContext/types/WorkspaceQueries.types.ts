// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type WorkspaceDisplayMetadataFragment = {
  __typename: 'RepositoryMetadata';
  key: string;
  value: string;
};

export type WorkspacePipelineFragment = {
  __typename: 'Pipeline';
  id: string;
  name: string;
  isJob: boolean;
  isAssetJob: boolean;
  externalJobSource: string | null;
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

export type WorkspacePartitionSetFragment = {
  __typename: 'PartitionSet';
  id: string;
  name: string;
  pipelineName: string;
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

export type PartialWorkspaceRepositoryFragment = {
  __typename: 'Repository';
  id: string;
  name: string;
  pipelines: Array<{
    __typename: 'Pipeline';
    id: string;
    name: string;
    isJob: boolean;
    isAssetJob: boolean;
    externalJobSource: string | null;
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
    name: string;
    pipelineName: string;
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

export type PartialWorkspaceLocationFragment = {
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
      externalJobSource: string | null;
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
      name: string;
      pipelineName: string;
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

export type PartialWorkspaceLocationNodeFragment = {
  __typename: 'WorkspaceLocationEntry';
  id: string;
  name: string;
  loadStatus: Types.RepositoryLocationLoadStatus;
  updatedTimestamp: number;
  versionKey: string;
  displayMetadata: Array<{__typename: 'RepositoryMetadata'; key: string; value: string}>;
  featureFlags: Array<{__typename: 'FeatureFlag'; name: string; enabled: boolean}>;
  stateVersions: {
    __typename: 'StateVersions';
    versionInfo: Array<{
      __typename: 'StateVersionInfo';
      name: string;
      version: string | null;
      createTimestamp: number | null;
    }>;
  } | null;
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
            externalJobSource: string | null;
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
            name: string;
            pipelineName: string;
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

export type LocationStatusEntryFragment = {
  __typename: 'WorkspaceLocationStatusEntry';
  id: string;
  name: string;
  loadStatus: Types.RepositoryLocationLoadStatus;
  updateTimestamp: number;
  versionKey: string;
};

export type WorkspaceAssetFragment = {
  __typename: 'AssetNode';
  id: string;
  graphName: string | null;
  opVersion: string | null;
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
  dependencyKeys: Array<{__typename: 'AssetKey'; path: Array<string>}>;
  dependedByKeys: Array<{__typename: 'AssetKey'; path: Array<string>}>;
  assetKey: {__typename: 'AssetKey'; path: Array<string>};
  internalFreshnessPolicy:
    | {
        __typename: 'CronFreshnessPolicy';
        deadlineCron: string;
        lowerBoundDeltaSeconds: number;
        timezone: string;
      }
    | {
        __typename: 'TimeWindowFreshnessPolicy';
        failWindowSeconds: number;
        warnWindowSeconds: number | null;
      }
    | null;
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
};

export type WorkspaceRepositoryAssetsFragment = {
  __typename: 'Repository';
  id: string;
  name: string;
  assetNodes: Array<{
    __typename: 'AssetNode';
    id: string;
    graphName: string | null;
    opVersion: string | null;
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
    dependencyKeys: Array<{__typename: 'AssetKey'; path: Array<string>}>;
    dependedByKeys: Array<{__typename: 'AssetKey'; path: Array<string>}>;
    assetKey: {__typename: 'AssetKey'; path: Array<string>};
    internalFreshnessPolicy:
      | {
          __typename: 'CronFreshnessPolicy';
          deadlineCron: string;
          lowerBoundDeltaSeconds: number;
          timezone: string;
        }
      | {
          __typename: 'TimeWindowFreshnessPolicy';
          failWindowSeconds: number;
          warnWindowSeconds: number | null;
        }
      | null;
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
  assetGroups: Array<{__typename: 'AssetGroup'; id: string; groupName: string}>;
};

export type WorkspaceAssetGroupFragment = {__typename: 'AssetGroup'; id: string; groupName: string};

export type WorkspaceLocationAssetsFragment = {
  __typename: 'RepositoryLocation';
  id: string;
  name: string;
  repositories: Array<{
    __typename: 'Repository';
    id: string;
    name: string;
    assetNodes: Array<{
      __typename: 'AssetNode';
      id: string;
      graphName: string | null;
      opVersion: string | null;
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
      dependencyKeys: Array<{__typename: 'AssetKey'; path: Array<string>}>;
      dependedByKeys: Array<{__typename: 'AssetKey'; path: Array<string>}>;
      assetKey: {__typename: 'AssetKey'; path: Array<string>};
      internalFreshnessPolicy:
        | {
            __typename: 'CronFreshnessPolicy';
            deadlineCron: string;
            lowerBoundDeltaSeconds: number;
            timezone: string;
          }
        | {
            __typename: 'TimeWindowFreshnessPolicy';
            failWindowSeconds: number;
            warnWindowSeconds: number | null;
          }
        | null;
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
    assetGroups: Array<{__typename: 'AssetGroup'; id: string; groupName: string}>;
  }>;
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
      externalJobSource: string | null;
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
      name: string;
      pipelineName: string;
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
    assetNodes: Array<{
      __typename: 'AssetNode';
      id: string;
      graphName: string | null;
      opVersion: string | null;
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
      dependencyKeys: Array<{__typename: 'AssetKey'; path: Array<string>}>;
      dependedByKeys: Array<{__typename: 'AssetKey'; path: Array<string>}>;
      assetKey: {__typename: 'AssetKey'; path: Array<string>};
      internalFreshnessPolicy:
        | {
            __typename: 'CronFreshnessPolicy';
            deadlineCron: string;
            lowerBoundDeltaSeconds: number;
            timezone: string;
          }
        | {
            __typename: 'TimeWindowFreshnessPolicy';
            failWindowSeconds: number;
            warnWindowSeconds: number | null;
          }
        | null;
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
    assetGroups: Array<{__typename: 'AssetGroup'; id: string; groupName: string}>;
    location: {__typename: 'RepositoryLocation'; id: string; name: string};
    displayMetadata: Array<{__typename: 'RepositoryMetadata'; key: string; value: string}>;
  }>;
};

export type WorkspaceLocationAssetsEntryFragment = {
  __typename: 'WorkspaceLocationEntry';
  id: string;
  name: string;
  loadStatus: Types.RepositoryLocationLoadStatus;
  updatedTimestamp: number;
  versionKey: string;
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
        repositories: Array<{
          __typename: 'Repository';
          id: string;
          name: string;
          assetNodes: Array<{
            __typename: 'AssetNode';
            id: string;
            graphName: string | null;
            opVersion: string | null;
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
            dependencyKeys: Array<{__typename: 'AssetKey'; path: Array<string>}>;
            dependedByKeys: Array<{__typename: 'AssetKey'; path: Array<string>}>;
            assetKey: {__typename: 'AssetKey'; path: Array<string>};
            internalFreshnessPolicy:
              | {
                  __typename: 'CronFreshnessPolicy';
                  deadlineCron: string;
                  lowerBoundDeltaSeconds: number;
                  timezone: string;
                }
              | {
                  __typename: 'TimeWindowFreshnessPolicy';
                  failWindowSeconds: number;
                  warnWindowSeconds: number | null;
                }
              | null;
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
          assetGroups: Array<{__typename: 'AssetGroup'; id: string; groupName: string}>;
        }>;
      }
    | null;
};

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
        stateVersions: {
          __typename: 'StateVersions';
          versionInfo: Array<{
            __typename: 'StateVersionInfo';
            name: string;
            version: string | null;
            createTimestamp: number | null;
          }>;
        } | null;
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
                  externalJobSource: string | null;
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
                  name: string;
                  pipelineName: string;
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

export type WorkspaceLatestStateVersionsQueryVariables = Types.Exact<{[key: string]: never}>;

export type WorkspaceLatestStateVersionsQuery = {
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
        latestStateVersions: {
          __typename: 'StateVersions';
          versionInfo: Array<{
            __typename: 'StateVersionInfo';
            name: string;
            version: string | null;
            createTimestamp: number | null;
          }>;
        } | null;
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

export type LocationWorkspaceAssetsQueryVariables = Types.Exact<{
  name: Types.Scalars['String']['input'];
}>;

export type LocationWorkspaceAssetsQuery = {
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
              repositories: Array<{
                __typename: 'Repository';
                id: string;
                name: string;
                assetNodes: Array<{
                  __typename: 'AssetNode';
                  id: string;
                  graphName: string | null;
                  opVersion: string | null;
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
                  dependencyKeys: Array<{__typename: 'AssetKey'; path: Array<string>}>;
                  dependedByKeys: Array<{__typename: 'AssetKey'; path: Array<string>}>;
                  assetKey: {__typename: 'AssetKey'; path: Array<string>};
                  internalFreshnessPolicy:
                    | {
                        __typename: 'CronFreshnessPolicy';
                        deadlineCron: string;
                        lowerBoundDeltaSeconds: number;
                        timezone: string;
                      }
                    | {
                        __typename: 'TimeWindowFreshnessPolicy';
                        failWindowSeconds: number;
                        warnWindowSeconds: number | null;
                      }
                    | null;
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
                assetGroups: Array<{__typename: 'AssetGroup'; id: string; groupName: string}>;
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
  stateVersions: {
    __typename: 'StateVersions';
    versionInfo: Array<{
      __typename: 'StateVersionInfo';
      name: string;
      version: string | null;
      createTimestamp: number | null;
    }>;
  } | null;
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
        isReloadSupported: boolean;
        serverId: string | null;
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
            externalJobSource: string | null;
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
            name: string;
            pipelineName: string;
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
          assetNodes: Array<{
            __typename: 'AssetNode';
            id: string;
            graphName: string | null;
            opVersion: string | null;
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
            dependencyKeys: Array<{__typename: 'AssetKey'; path: Array<string>}>;
            dependedByKeys: Array<{__typename: 'AssetKey'; path: Array<string>}>;
            assetKey: {__typename: 'AssetKey'; path: Array<string>};
            internalFreshnessPolicy:
              | {
                  __typename: 'CronFreshnessPolicy';
                  deadlineCron: string;
                  lowerBoundDeltaSeconds: number;
                  timezone: string;
                }
              | {
                  __typename: 'TimeWindowFreshnessPolicy';
                  failWindowSeconds: number;
                  warnWindowSeconds: number | null;
                }
              | null;
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
          assetGroups: Array<{__typename: 'AssetGroup'; id: string; groupName: string}>;
          location: {__typename: 'RepositoryLocation'; id: string; name: string};
          displayMetadata: Array<{__typename: 'RepositoryMetadata'; key: string; value: string}>;
        }>;
        dagsterLibraryVersions: Array<{
          __typename: 'DagsterLibraryVersion';
          name: string;
          version: string;
        }> | null;
      }
    | null;
};

export type WorkspaceRepositoryLocationFragment = {
  __typename: 'RepositoryLocation';
  id: string;
  name: string;
  isReloadSupported: boolean;
  serverId: string | null;
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
      externalJobSource: string | null;
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
      name: string;
      pipelineName: string;
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
    assetNodes: Array<{
      __typename: 'AssetNode';
      id: string;
      graphName: string | null;
      opVersion: string | null;
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
      dependencyKeys: Array<{__typename: 'AssetKey'; path: Array<string>}>;
      dependedByKeys: Array<{__typename: 'AssetKey'; path: Array<string>}>;
      assetKey: {__typename: 'AssetKey'; path: Array<string>};
      internalFreshnessPolicy:
        | {
            __typename: 'CronFreshnessPolicy';
            deadlineCron: string;
            lowerBoundDeltaSeconds: number;
            timezone: string;
          }
        | {
            __typename: 'TimeWindowFreshnessPolicy';
            failWindowSeconds: number;
            warnWindowSeconds: number | null;
          }
        | null;
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
    assetGroups: Array<{__typename: 'AssetGroup'; id: string; groupName: string}>;
    location: {__typename: 'RepositoryLocation'; id: string; name: string};
    displayMetadata: Array<{__typename: 'RepositoryMetadata'; key: string; value: string}>;
  }>;
  dagsterLibraryVersions: Array<{
    __typename: 'DagsterLibraryVersion';
    name: string;
    version: string;
  }> | null;
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
    externalJobSource: string | null;
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
    name: string;
    pipelineName: string;
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
  assetNodes: Array<{
    __typename: 'AssetNode';
    id: string;
    graphName: string | null;
    opVersion: string | null;
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
    dependencyKeys: Array<{__typename: 'AssetKey'; path: Array<string>}>;
    dependedByKeys: Array<{__typename: 'AssetKey'; path: Array<string>}>;
    assetKey: {__typename: 'AssetKey'; path: Array<string>};
    internalFreshnessPolicy:
      | {
          __typename: 'CronFreshnessPolicy';
          deadlineCron: string;
          lowerBoundDeltaSeconds: number;
          timezone: string;
        }
      | {
          __typename: 'TimeWindowFreshnessPolicy';
          failWindowSeconds: number;
          warnWindowSeconds: number | null;
        }
      | null;
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
  assetGroups: Array<{__typename: 'AssetGroup'; id: string; groupName: string}>;
  location: {__typename: 'RepositoryLocation'; id: string; name: string};
  displayMetadata: Array<{__typename: 'RepositoryMetadata'; key: string; value: string}>;
};

export const LocationWorkspaceQueryVersion = '5d21d0e8b4e77431881531cb470781a940ecf33d3f63759ff6d702264687e717';

export const WorkspaceLatestStateVersionsQueryVersion = 'f1ce8eed86770d66db48c8d69383638f4c61ddba7625f396d602292666d868e5';

export const CodeLocationStatusQueryVersion = '5491629a2659feca3a6cf0cc976c6f59c8e78dff1193e07d7850ae4355698b04';

export const LocationWorkspaceAssetsQueryVersion = '3e053c920a3fd3448cf3cb0ee19ab1b643c66ecde751bb81d464b6e75e046d3f';
