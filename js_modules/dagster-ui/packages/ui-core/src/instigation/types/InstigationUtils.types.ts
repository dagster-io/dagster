// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RunStatusFragment = {__typename: 'Run'; id: string; status: Types.RunStatus};

export type InstigationStateFragment = {
  __typename: 'InstigationState';
  id: string;
  selectorId: string;
  name: string;
  instigationType: Types.InstigationType;
  status: Types.InstigationStatus;
  hasStartPermission: boolean;
  hasStopPermission: boolean;
  repositoryName: string;
  repositoryLocationName: string;
  runningCount: number;
  typeSpecificData:
    | {__typename: 'ScheduleData'; cronSchedule: string}
    | {__typename: 'SensorData'; lastRunKey: string | null; lastCursor: string | null}
    | null;
  runs: Array<{
    __typename: 'Run';
    id: string;
    status: Types.RunStatus;
    creationTime: number;
    startTime: number | null;
    endTime: number | null;
    updateTime: number | null;
  }>;
  ticks: Array<{
    __typename: 'InstigationTick';
    id: string;
    cursor: string | null;
    status: Types.InstigationTickStatus;
    timestamp: number;
    skipReason: string | null;
    runIds: Array<string>;
    runKeys: Array<string>;
    error: {
      __typename: 'PythonError';
      message: string;
      stack: Array<string>;
      errorChain: Array<{
        __typename: 'ErrorChainLink';
        isExplicitLink: boolean;
        error: {__typename: 'PythonError'; message: string; stack: Array<string>};
      }>;
    } | null;
  }>;
};

export type DynamicPartitionsRequestResultFragment = {
  __typename: 'DynamicPartitionsRequestResult';
  partitionsDefName: string;
  partitionKeys: Array<string> | null;
  skippedPartitionKeys: Array<string>;
  type: Types.DynamicPartitionsRequestType;
};

export type HistoryTickFragment = {
  __typename: 'InstigationTick';
  id: string;
  tickId: string;
  status: Types.InstigationTickStatus;
  timestamp: number;
  endTimestamp: number | null;
  cursor: string | null;
  instigationType: Types.InstigationType;
  skipReason: string | null;
  requestedAssetMaterializationCount: number;
  runIds: Array<string>;
  originRunIds: Array<string>;
  logKey: Array<string> | null;
  runKeys: Array<string>;
  runs: Array<{__typename: 'Run'; id: string; status: Types.RunStatus}>;
  error: {
    __typename: 'PythonError';
    message: string;
    stack: Array<string>;
    errorChain: Array<{
      __typename: 'ErrorChainLink';
      isExplicitLink: boolean;
      error: {__typename: 'PythonError'; message: string; stack: Array<string>};
    }>;
  } | null;
  dynamicPartitionsRequestResults: Array<{
    __typename: 'DynamicPartitionsRequestResult';
    partitionsDefName: string;
    partitionKeys: Array<string> | null;
    skippedPartitionKeys: Array<string>;
    type: Types.DynamicPartitionsRequestType;
  }>;
};
