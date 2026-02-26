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
            hasStartPermission: boolean;
            hasStopPermission: boolean;
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
            hasStartPermission: boolean;
            hasStopPermission: boolean;
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
          hasStartPermission: boolean;
          hasStopPermission: boolean;
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
          hasStartPermission: boolean;
          hasStopPermission: boolean;
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
    hasStartPermission: boolean;
    hasStopPermission: boolean;
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
    hasStartPermission: boolean;
    hasStopPermission: boolean;
    typeSpecificData:
      | {__typename: 'ScheduleData'}
      | {__typename: 'SensorData'; lastCursor: string | null}
      | null;
  };
};

export type AssetInstigatorFragment =
  | AssetInstigatorFragment_Schedule
  | AssetInstigatorFragment_Sensor;

export const AssetAutomationQueryVersion = 'ba290842b1e65f256ea3b1e95285e050da5a8ee50ecf34b6228299e7dd605425';
