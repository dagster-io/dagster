// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetGraphQueryVariables = Types.Exact<{
  pipelineSelector?: Types.InputMaybe<Types.PipelineSelector>;
  groupSelector?: Types.InputMaybe<Types.AssetGroupSelector>;
}>;

export type AssetGraphQuery = {
  __typename: 'Query';
  assetNodes: Array<{
    __typename: 'AssetNode';
    id: string;
    groupName: string;
    isExecutable: boolean;
    changedReasons: Array<Types.ChangeReason>;
    hasMaterializePermission: boolean;
    graphName: string | null;
    jobNames: Array<string>;
    opNames: Array<string>;
    opVersion: string | null;
    description: string | null;
    computeKind: string | null;
    isPartitioned: boolean;
    isObservable: boolean;
    isMaterializable: boolean;
    isAutoCreatedStub: boolean;
    kinds: Array<string>;
    tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
    owners: Array<
      {__typename: 'TeamAssetOwner'; team: string} | {__typename: 'UserAssetOwner'; email: string}
    >;
    repository: {
      __typename: 'Repository';
      id: string;
      name: string;
      location: {__typename: 'RepositoryLocation'; id: string; name: string};
    };
    dependencyKeys: Array<{__typename: 'AssetKey'; path: Array<string>}>;
    dependedByKeys: Array<{__typename: 'AssetKey'; path: Array<string>}>;
    assetKey: {__typename: 'AssetKey'; path: Array<string>};
    targetingInstigators: Array<
      | {
          __typename: 'Schedule';
          id: string;
          name: string;
          cronSchedule: string;
          executionTimezone: string | null;
          scheduleState: {
            __typename: 'InstigationState';
            id: string;
            selectorId: string;
            status: Types.InstigationStatus;
          };
        }
      | {
          __typename: 'Sensor';
          id: string;
          name: string;
          sensorType: Types.SensorType;
          sensorState: {
            __typename: 'InstigationState';
            id: string;
            selectorId: string;
            status: Types.InstigationStatus;
            typeSpecificData:
              | {__typename: 'ScheduleData'}
              | {__typename: 'SensorData'; lastCursor: string | null}
              | null;
          };
        }
    >;
    automationCondition: {
      __typename: 'AutomationCondition';
      label: string | null;
      expandedLabel: Array<string>;
    } | null;
  }>;
};

export type AssetNodeForGraphQueryFragment = {
  __typename: 'AssetNode';
  id: string;
  groupName: string;
  isExecutable: boolean;
  changedReasons: Array<Types.ChangeReason>;
  hasMaterializePermission: boolean;
  graphName: string | null;
  jobNames: Array<string>;
  opNames: Array<string>;
  opVersion: string | null;
  description: string | null;
  computeKind: string | null;
  isPartitioned: boolean;
  isObservable: boolean;
  isMaterializable: boolean;
  isAutoCreatedStub: boolean;
  kinds: Array<string>;
  tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
  owners: Array<
    {__typename: 'TeamAssetOwner'; team: string} | {__typename: 'UserAssetOwner'; email: string}
  >;
  repository: {
    __typename: 'Repository';
    id: string;
    name: string;
    location: {__typename: 'RepositoryLocation'; id: string; name: string};
  };
  dependencyKeys: Array<{__typename: 'AssetKey'; path: Array<string>}>;
  dependedByKeys: Array<{__typename: 'AssetKey'; path: Array<string>}>;
  assetKey: {__typename: 'AssetKey'; path: Array<string>};
  targetingInstigators: Array<
    | {
        __typename: 'Schedule';
        id: string;
        name: string;
        cronSchedule: string;
        executionTimezone: string | null;
        scheduleState: {
          __typename: 'InstigationState';
          id: string;
          selectorId: string;
          status: Types.InstigationStatus;
        };
      }
    | {
        __typename: 'Sensor';
        id: string;
        name: string;
        sensorType: Types.SensorType;
        sensorState: {
          __typename: 'InstigationState';
          id: string;
          selectorId: string;
          status: Types.InstigationStatus;
          typeSpecificData:
            | {__typename: 'ScheduleData'}
            | {__typename: 'SensorData'; lastCursor: string | null}
            | null;
        };
      }
  >;
  automationCondition: {
    __typename: 'AutomationCondition';
    label: string | null;
    expandedLabel: Array<string>;
  } | null;
};

export const AssetGraphQueryVersion = '0eb1ea67919c50db776230ddbe23c2502578584270c9a995ecb37d84deff9713';
