/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type InstigationStatus = 'RUNNING' | 'STOPPED';

export type InstigationTickStatus = 'FAILURE' | 'SKIPPED' | 'STARTED' | 'SUCCESS';

export type InstigationType = 'AUTO_MATERIALIZE' | 'SCHEDULE' | 'SENSOR';

export type RunStatus =
  | 'CANCELED'
  | 'CANCELING'
  | 'FAILURE'
  | 'MANAGED'
  | 'NOT_STARTED'
  | 'QUEUED'
  | 'STARTED'
  | 'STARTING'
  | 'SUCCESS';

export type ScheduleFragment = {
  __typename: 'Schedule';
  id: string;
  name: string;
  cronSchedule: string;
  executionTimezone: string | null;
  pipelineName: string;
  solidSelection: Array<string | null> | null;
  mode: string;
  description: string | null;
  defaultStatus: Types.InstigationStatus;
  canReset: boolean;
  partitionSet: {__typename: 'PartitionSet'; id: string; name: string} | null;
  scheduleState: {
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
  futureTicks: {
    __typename: 'DryRunInstigationTicks';
    results: Array<{__typename: 'DryRunInstigationTick'; timestamp: number | null}>;
  };
  owners: Array<
    | {__typename: 'TeamDefinitionOwner'; team: string}
    | {__typename: 'UserDefinitionOwner'; email: string}
  >;
};
