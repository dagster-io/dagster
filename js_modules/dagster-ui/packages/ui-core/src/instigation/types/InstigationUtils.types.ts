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
