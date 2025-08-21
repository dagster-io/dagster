// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetAutomationQueryVariables = Types.Exact<{
  assetKeys: Array<Types.AssetKeyInput> | Types.AssetKeyInput;
}>;

export type AssetAutomationQuery = {
  __typename: 'Query';
  assetNodes: Array<{
    __typename: 'AssetNode';
    id: string;
    assetKey: {__typename: 'AssetKey'; path: Array<string>};
    automationCondition: {
      __typename: 'AutomationCondition';
      label: string | null;
      expandedLabel: Array<string>;
    } | null;
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
    lastAutoMaterializationEvaluationRecord: {
      __typename: 'AutoMaterializeAssetEvaluationRecord';
      id: string;
      evaluationId: string;
    } | null;
  }>;
};

export type AssetAutomationFragment = {
  __typename: 'AssetNode';
  assetKey: {__typename: 'AssetKey'; path: Array<string>};
  automationCondition: {
    __typename: 'AutomationCondition';
    label: string | null;
    expandedLabel: Array<string>;
  } | null;
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
  lastAutoMaterializationEvaluationRecord: {
    __typename: 'AutoMaterializeAssetEvaluationRecord';
    id: string;
    evaluationId: string;
  } | null;
};

export type AssetInstigatorFragment_Schedule = {
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
};

export type AssetInstigatorFragment_Sensor = {
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
};

export type AssetInstigatorFragment =
  | AssetInstigatorFragment_Schedule
  | AssetInstigatorFragment_Sensor;

export const AssetAutomationQueryVersion = '30c89838e2bb20980912b383d35a539fa7a67c6df4f721063f4321892d8ca647';
