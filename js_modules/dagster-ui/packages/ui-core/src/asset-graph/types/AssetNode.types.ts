// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetNodeFragment = {
  __typename: 'AssetNode';
  id: string;
  graphName: string | null;
  hasMaterializePermission: boolean;
  jobNames: Array<string>;
  changedReasons: Array<Types.ChangeReason>;
  opNames: Array<string>;
  opVersion: string | null;
  description: string | null;
  computeKind: string | null;
  isPartitioned: boolean;
  isObservable: boolean;
  isMaterializable: boolean;
  isAutoCreatedStub: boolean;
  kinds: Array<string>;
  owners: Array<
    {__typename: 'TeamAssetOwner'; team: string} | {__typename: 'UserAssetOwner'; email: string}
  >;
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
  tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
};

export type AssetNodeKeyFragment = {__typename: 'AssetKey'; path: Array<string>};
